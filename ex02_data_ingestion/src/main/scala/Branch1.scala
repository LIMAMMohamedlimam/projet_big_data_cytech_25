package fr.cytech.integration

import org.apache.spark.sql.{SparkSession, DataFrame, Column}
import org.apache.spark.sql.functions._

object Branch1 {

    val ValidVendorIDs = Seq(1, 2, 6, 7)
    val ValidRateCodes = Seq(1, 2, 3, 4, 5, 6, 99)
    val MaxDistance = 200.0
    val MaxFare = 1000.0
    val MaxTotal = 1500.0
    val SurchargeTolerance = 0.50

    def main(args: Array[String]): Unit = {

        val spark = SparkSession.builder()
        .appName("SparkApp")
        .master("local")
        .config("fs.s3a.access.key", "minio")
        .config("fs.s3a.secret.key", "minio123")
        .config("fs.s3a.endpoint", "http://localhost:9000/")
        .config("fs.s3a.path.style.access", "true")
        .config("fs.s3a.connection.ssl.enable", "false")
        .config("fs.s3a.attempts.maximum", "1")
        .config("fs.s3a.connection.establish.timeout", "6000")
        .config("fs.s3a.connection.timeout", "5000")
        .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")

        try {
        val inputPath = "s3a://nyc-raw/yellow_tripdata_2025-11.parquet"
        println(s"Lecture des données depuis $inputPath")

        val rawDF = spark.read.parquet(inputPath)
        val initialCount = rawDF.count()
        println(s"Nombre de lignes initiales: $initialCount")

        val cleanedDF = validateAndCleanData(rawDF)
        val cleanedCount = cleanedDF.count()

        println(s"Nombre de lignes après validation: $cleanedCount")
        println(s"Lignes supprimées: ${initialCount - cleanedCount}")
        println(s"Taux de conservation: ${(cleanedCount.toDouble / initialCount * 100).formatted("%.2f")}%")

        val outputPath = "s3a://nyc-cleaned/yellow_tripdata_cleaned_2024-01.parquet"
        println(s"Écriture des données nettoyées vers $outputPath")

        cleanedDF.write.mode("overwrite").parquet(outputPath)

        println("BRANCHE 1 - Terminé avec succès!")

        } finally {
        spark.stop()
        }
    }

    // 1. VendorID Validation
    def isValidVendor: Column =
        col("VendorID").isin(ValidVendorIDs: _*)

    // 2. Timestamp Validation
    def areTimestampsValid: Column =
        col("tpep_pickup_datetime").isNotNull &&
        col("tpep_dropoff_datetime").isNotNull &&
        col("tpep_pickup_datetime") < col("tpep_dropoff_datetime")

    // 3. Passenger Count Validation
    def isPassengerCountValid: Column =
        col("passenger_count").between(0, 9)

    // 4. Trip Distance Validation
    def isTripDistanceValid: Column =
        col("trip_distance").between(0, MaxDistance)

    // 5. Total Amount Coherence Validation
    def isTotalAmountCoherent: Column = {
        val components =
        col("fare_amount") +
            col("extra") +
            col("mta_tax") +
            col("tip_amount") +
            col("tolls_amount") +
            col("improvement_surcharge") +
            coalesce(col("congestion_surcharge"), lit(0.0)) +
            coalesce(col("airport_fee"), lit(0.0)) +
            coalesce(col("cbd_congestion_fee"), lit(0.0))

        abs(col("total_amount") - components) <= SurchargeTolerance
    }

    def validateAndCleanData(df: DataFrame): DataFrame = {
        println("Application des validations selon le contrat NYC TLC...")

        val cleaned = df
        .filter(isValidVendor)
        .filter(areTimestampsValid)
        .filter(isPassengerCountValid)
        .filter(isTripDistanceValid)
        .filter(col("RatecodeID").isin(ValidRateCodes: _*))
        .filter(col("store_and_fwd_flag").isin("Y", "N"))
        .filter(col("payment_type").isin(0, 1, 2, 3, 4, 5, 6))
        .filter(col("fare_amount").between(0, MaxFare))
        .filter(col("total_amount").between(0.01, MaxTotal))
        .filter(isTotalAmountCoherent)

        println("Validation et nettoyage des données selon le contrat NYC TLC terminé!")
        cleaned
    }
  
}
