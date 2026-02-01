import org.apache.spark.sql.{SparkSession , DataFrame}
import java.io.{File, FileOutputStream}
import java.nio.file.{Files, Paths}
import java.net.URL
import java.nio.channels.Channels

object Main {
  
  def main(args: Array[String]): Unit = {
    
    // Configuration Spark avec MinIO
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
    
    try {
        // PARTIE 1: Télécharger le fichier parquet dans data/raw
        val fileName = "yellow_tripdata_2025-11.parquet"
        val url = s"https://d37ci6vzurychx.cloudfront.net/trip-data/$fileName"
        val localPath = s"data/raw/$fileName"

        val path = Paths.get(localPath)

        if (Files.exists(path)) {
            println(s"Le fichier $fileName existe déjà dans $localPath, téléchargement ignoré.")
        } else {
            println(s"Téléchargement de $fileName...")
            downloadFile(url, localPath)
            println(s"Fichier téléchargé dans $localPath")
        }
        
        // PARTIE 2: Upload vers MinIO bucket nyc_raw
        uploadToMinio(spark, localPath, fileName)
        
        // PARTIE 3: Téléchargement direct vers MinIO (sans passer par local)
        downloadDirectlyToMinio(spark, url, fileName)
      
    } finally {
      spark.stop()
    }
  }
  
  /**
   * Télécharge un fichier depuis une URL vers un chemin local
   */
  def downloadFile(url: String, localPath: String): Unit = {
    val file = new File(localPath)
    file.getParentFile.mkdirs()
    
    val website = new URL(url)
    val rbc = Channels.newChannel(website.openStream())
    val fos = new FileOutputStream(file)
    
    try {
      fos.getChannel.transferFrom(rbc, 0, Long.MaxValue)
    } finally {
      fos.close()
      rbc.close()
    }
  }
  
  /**
   * Upload un fichier local vers MinIO
   */
  def uploadToMinio(spark: SparkSession, localPath: String, fileName: String): Unit = {
    println(s"Upload de $fileName vers MinIO...")
    
    val df = spark.read.parquet(localPath)
    df.write
      .mode("overwrite")
      .parquet(s"s3a://nyc-raw//$fileName")
    
    println(s"Fichier uploadé dans MinIO bucket nyc-raw")
  }
  
  /**
   * Téléchargement direct vers MinIO sans stockage local intermédiaire
   */
  def downloadDirectlyToMinio(spark: SparkSession, url: String, fileName: String): Unit = {
    println(s"Téléchargement direct vers MinIO...")
    
    // Lire directement depuis l'URL et écrire dans MinIO
    val df = spark.read.parquet(url)
    df.write
      .mode("overwrite")
      .parquet(s"s3a://nyc-raw/direct_$fileName")
    
    println(s"Téléchargement direct terminé dans MinIO")
  }
}