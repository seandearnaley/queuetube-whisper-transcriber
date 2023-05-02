import { useState } from "react";
import { useForm } from "react-hook-form";
import styles from "./index.module.css";

const Home = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();
  const [message, setMessage] = useState("");
  const [processingMessage, setProcessingMessage] = useState("");

  const onSubmit = async (data) => {
    const response = await fetch("http://localhost:8000/download_url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: data.url }),
    });
    const responseData = await response.json();
    setMessage(responseData.message);
  };

  const handleProcessVideos = async () => {
    const response = await fetch(
      "http://localhost:8000/process_untranscribed_videos",
      {
        method: "POST",
      }
    );
    const data = await response.json();
    setProcessingMessage(data.message);
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Whisper Transcriber</h1>
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)}>
        <label className={styles.label} htmlFor="url">
          YouTube Channel URL:
        </label>
        <input
          className={styles.input}
          type="text"
          id="url"
          {...register("url", {
            required: "URL is required",
            pattern: {
              value: /^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/,
              message: "Invalid YouTube URL",
            },
          })}
        />
        {errors.url && (
          <p className={styles["error-message"]}>{errors.url.message}</p>
        )}
        <button className={styles.button} type="submit">
          Download
        </button>
      </form>

      {message && <p>{message}</p>}
      <button className={styles.button} onClick={handleProcessVideos}>
        Process Untranscribed Videos
      </button>
      {processingMessage && <p>{processingMessage}</p>}
    </div>
  );
};

export default Home;
