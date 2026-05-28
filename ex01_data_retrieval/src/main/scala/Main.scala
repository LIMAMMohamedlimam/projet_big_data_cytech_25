import org.apache.spark.sql.{SparkSession , DataFrame}
import java.io.{File, FileOutputStream}
import java.nio.file.{Files, Paths}
import java.net.{URL, URI}
import java.nio.channels.Channels

import io.minio.{MinioClient, PutObjectArgs}
import java.net.http.{HttpClient, HttpRequest, HttpResponse}
import java.time.Duration

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
        // TODO: dynamicaly be able to change month and year
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
        
        // // PARTIE 2: Upload vers MinIO bucket nyc_raw
        // uploadToMinio(spark, localPath, fileName)
        
        // // PARTIE 3: Téléchargement direct vers MinIO (sans passer par local)
        // downloadDirectlyToMinio(spark, url, fileName)

        streamParquetToMinio(
          parquetUrl = url,
          bucket = "nyc-raw",
          objectKey = s"$fileName",
          minioEndpoint = "http://localhost:9000",
          accessKey = "minio",
          secretKey = "minio123",
          insecure = true
        )
      
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


  def streamParquetToMinio(
    parquetUrl: String,
    bucket: String,
    objectKey: String,
    minioEndpoint: String,
    accessKey: String,
    secretKey: String,
    insecure: Boolean = false
  ): Unit = {

    println(s"Streaming $parquetUrl to MinIO s3://$bucket/$objectKey")

    val minio = MinioClient.builder()
      .endpoint(minioEndpoint)
      .credentials(accessKey, secretKey)
      .build()

    // HTTP stream (no buffering to disk)
    val http = HttpClient.newBuilder()
      .connectTimeout(Duration.ofSeconds(20))
      .followRedirects(HttpClient.Redirect.NORMAL)
      .build()

    val req = HttpRequest.newBuilder()
      .uri(URI.create(parquetUrl))
      .timeout(Duration.ofMinutes(5))
      .GET()
      .build()

    val resp = http.send(req, HttpResponse.BodyHandlers.ofInputStream())

    if (resp.statusCode() / 100 != 2) {
      val code = resp.statusCode()
      resp.body().close()
      throw new RuntimeException(s"HTTP download failed: status=$code url=$parquetUrl")
    }

    val in = resp.body() // InputStream
    try {
      // content-length if provided (better), else -1 (unknown)
      val len =
        resp.headers().firstValueAsLong("content-length").orElse(-1L)

      minio.putObject(
        PutObjectArgs.builder()
          .bucket(bucket)
          .`object`(objectKey)
          .stream(in, len, 10 * 1024 * 1024) // partSize=10MB
          .contentType("application/octet-stream") // or "application/vnd.apache.parquet"
          .build()
      )
    } finally {
      in.close()
    }
  }
}