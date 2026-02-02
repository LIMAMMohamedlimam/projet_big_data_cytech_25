package fr.cytech.integration

import org.apache.spark.sql.{SparkSession, DataFrame, SaveMode}
import org.apache.spark.sql.functions._
import java.sql.{Connection, DriverManager, PreparedStatement, ResultSet}
import java.util.Properties
import scala.collection.mutable

object Branch2 {
  
  // Configuration PostgreSQL
  val POSTGRES_URL = "jdbc:postgresql://localhost:5432/nyc_taxi_pro_big_data"
  val POSTGRES_USER = "admin"
  val POSTGRES_PASSWORD = "admin123"
  
  def main(args: Array[String]): Unit = {
    
    val spark = SparkSession.builder()
        .appName("SparkApp")
        .master("local")
        .config("fs.s3a.access.key", "minio")
        .config("fs.s3a.secret.key", "minio123")
        .config("fs.s3a.endpoint", "http://localhost:9000/") // A changer lors du déploiement
        .config("fs.s3a.path.style.access", "true")
        .config("fs.s3a.connection.ssl.enable", "false")
        .config("fs.s3a.attempts.maximum", "1")
        .config("fs.s3a.connection.establish.timeout", "6000")
        .config("fs.s3a.connection.timeout", "5000")
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    
    import spark.implicits._
    
    try {
      println("========== BRANCHE 2: INGESTION POSTGRESQL ==========\n")
      
      // 1. Lecture des données nettoyées depuis MinIO
      val cleanedPath = "s3a://nyc-cleaned/yellow_tripdata_cleaned_2024-01.parquet"
      println(s"Lecture des données depuis: $cleanedPath")
      val cleanedDF = spark.read.parquet(cleanedPath)
      val totalRows = cleanedDF.count()
      println(s"Nombre de lignes à ingérer: $totalRows\n")
      
      // 2. Charger les caches des dimensions depuis PostgreSQL
      println("Chargement des dimensions depuis PostgreSQL...")
      val dimCaches = new DimensionCaches(POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD)
      
      // 3. Transformation: Enrichissement avec clés de dimension
      println("Transformation et enrichissement des données...\n")
      val enrichedDF = enrichWithDimensionKeys(cleanedDF, dimCaches, spark)
      
      // 4. Ingestion vers PostgreSQL
      println("Ingestion vers PostgreSQL (fact_trips)...")
      ingestToPostgres(enrichedDF, spark)
      
      println("\n========== BRANCHE 2 TERMINÉE AVEC SUCCÈS ==========")
      
      
    } finally {
      spark.stop()
    }
  }
  
  /**
   * Enrichit le DataFrame avec les clés de dimension
   */
  def enrichWithDimensionKeys(df: DataFrame, dimCaches: DimensionCaches, spark: SparkSession): DataFrame = {
    import spark.implicits._
    
    // Broadcast des dimensions pour performance
    val vendorMap = spark.sparkContext.broadcast(dimCaches.vendorCache)
    val paymentMap = spark.sparkContext.broadcast(dimCaches.paymentCache)
    val rateMap = spark.sparkContext.broadcast(dimCaches.rateCache)
    val locationMap = spark.sparkContext.broadcast(dimCaches.locationCache)
    val dateMap = spark.sparkContext.broadcast(dimCaches.dateCache)
    val timeMap = spark.sparkContext.broadcast(dimCaches.timeCache)
    
    // UDF pour lookup des dimensions
    val lookupVendor = udf((vendorId: Int) => vendorMap.value.getOrElse(vendorId, -1))
    val lookupPayment = udf((paymentType: Int) => paymentMap.value.getOrElse(paymentType, -1))
    val lookupRate = udf((rateId: Int) => rateMap.value.getOrElse(rateId, -1))
    val lookupLocation = udf((locationId: Int) => locationMap.value.getOrElse(locationId, -1))
    val lookupDate = udf((date: String) => dateMap.value.getOrElse(date, -1))
    val lookupTime = udf((time: String) => timeMap.value.getOrElse(time, -1))
    
    df
      // Clés de dimension simples
      .withColumn("vendor_key", lookupVendor($"VendorID"))
      .withColumn("payment_key", lookupPayment($"payment_type"))
      .withColumn("rate_key", lookupRate($"RatecodeID"))
      .withColumn("pickup_location_key", lookupLocation($"PULocationID"))
      .withColumn("dropoff_location_key", lookupLocation($"DOLocationID"))
      
      // Dimensions temporelles: séparer date et time
      .withColumn("pickup_date_key", lookupDate(
        date_format($"tpep_pickup_datetime", "yyyy-MM-dd")
      ))
      .withColumn("pickup_time_key", lookupTime(
        date_format($"tpep_pickup_datetime", "HH:mm:00")
      ))
      .withColumn("dropoff_date_key", lookupDate(
        date_format($"tpep_dropoff_datetime", "yyyy-MM-dd")
      ))
      .withColumn("dropoff_time_key", lookupTime(
        date_format($"tpep_dropoff_datetime", "HH:mm:00")
      ))
      
      // Calculer trip_duration en minutes
      .withColumn("trip_duration_minutes", 
        (unix_timestamp($"tpep_dropoff_datetime") - 
         unix_timestamp($"tpep_pickup_datetime")) / 60
      )
      
      // Filtrer les lignes avec clés invalides (-1)
      .filter(
        $"vendor_key" =!= -1 &&
        $"payment_key" =!= -1 &&
        $"rate_key" =!= -1 &&
        $"pickup_location_key" =!= -1 &&
        $"dropoff_location_key" =!= -1 &&
        $"pickup_date_key" =!= -1 &&
        $"pickup_time_key" =!= -1 &&
        $"dropoff_date_key" =!= -1 &&
        $"dropoff_time_key" =!= -1
      )
      
      // Sélectionner les colonnes finales pour fact_trips
      .select(
        $"vendor_key",
        $"pickup_date_key",
        $"pickup_time_key",
        $"dropoff_date_key",
        $"dropoff_time_key",
        $"pickup_location_key",
        $"dropoff_location_key",
        $"payment_key",
        $"rate_key",
        $"passenger_count",
        $"trip_distance",
        $"trip_duration_minutes".cast("int"),
        $"fare_amount",
        $"extra",
        $"mta_tax",
        $"tip_amount",
        $"tolls_amount",
        $"improvement_surcharge",
        $"total_amount",
        coalesce($"congestion_surcharge", lit(0.0)).as("congestion_surcharge"),
        coalesce($"airport_fee", lit(0.0)).as("airport_fee"),
        coalesce($"cbd_congestion_fee", lit(0.0)).as("cbd_congestion_fee"),
        $"store_and_fwd_flag"
      )
  }
  
  /**
   * Ingère les données enrichies vers PostgreSQL
   */
  def ingestToPostgres(df: DataFrame, spark: SparkSession): Unit = {
    val props = new Properties()
    props.setProperty("user", POSTGRES_USER)
    props.setProperty("password", POSTGRES_PASSWORD)
    props.setProperty("driver", "org.postgresql.Driver")
    
    // Batch insert pour performance
    df.write
      .mode(SaveMode.Append)
      .jdbc(POSTGRES_URL, "fact_trips", props)
    
    val insertedCount = df.count()
    println(s"✓ $insertedCount lignes insérées dans fact_trips")
  }
  
}

/**
 * Classe pour gérer les caches des tables de dimension
 */
class DimensionCaches(url: String, user: String, password: String) {
  
  private var connection: Connection = _
  
  // Caches: Map[business_key, surrogate_key]
  val vendorCache: Map[Int, Int] = loadVendorCache()
  val paymentCache: Map[Int, Int] = loadPaymentCache()
  val rateCache: Map[Int, Int] = loadRateCache()
  val locationCache: Map[Int, Int] = loadLocationCache()
  val dateCache: Map[String, Int] = loadDateCache()
  val timeCache: Map[String, Int] = loadTimeCache()
  
  private def getConnection: Connection = {
    Class.forName("org.postgresql.Driver")
    DriverManager.getConnection(url, user, password)
  }
  
  private def loadVendorCache(): Map[Int, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT vendor_id, vendor_key FROM dim_vendor")
    val cache = mutable.Map[Int, Int]()
    while (rs.next()) {
      cache(rs.getInt("vendor_id")) = rs.getInt("vendor_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_vendor: ${cache.size} entrées chargées")
    cache.toMap
  }
  
  private def loadPaymentCache(): Map[Int, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT payment_type, payment_key FROM dim_payment")
    val cache = mutable.Map[Int, Int]()
    while (rs.next()) {
      cache(rs.getInt("payment_type")) = rs.getInt("payment_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_payment: ${cache.size} entrées chargées")
    cache.toMap
  }
  
  private def loadRateCache(): Map[Int, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT rate_code_id, rate_key FROM dim_rate")
    val cache = mutable.Map[Int, Int]()
    while (rs.next()) {
      cache(rs.getInt("rate_code_id")) = rs.getInt("rate_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_rate: ${cache.size} entrées chargées")
    cache.toMap
  }
  
  private def loadLocationCache(): Map[Int, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT location_id, location_key FROM dim_location")
    val cache = mutable.Map[Int, Int]()
    while (rs.next()) {
      cache(rs.getInt("location_id")) = rs.getInt("location_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_location: ${cache.size} entrées chargées")
    cache.toMap
  }
  
  private def loadDateCache(): Map[String, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT date_value, date_key FROM dim_date")
    val cache = mutable.Map[String, Int]()
    while (rs.next()) {
      cache(rs.getDate("date_value").toString) = rs.getInt("date_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_date: ${cache.size} entrées chargées")
    cache.toMap
  }
  
  private def loadTimeCache(): Map[String, Int] = {
    val conn = getConnection
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT time_value, time_key FROM dim_time")
    val cache = mutable.Map[String, Int]()
    while (rs.next()) {
      cache(rs.getTime("time_value").toString) = rs.getInt("time_key")
    }
    rs.close()
    stmt.close()
    conn.close()
    println(s"  ✓ dim_time: ${cache.size} entrées chargées")
    cache.toMap
  }
}
