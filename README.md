# QueueTube Whisper Transcriber

A high-performance, CPU-optimized Docker-based service for downloading YouTube videos and transcribing them using OpenAI's Whisper ASR system. Built with FastAPI, Celery, and Redis for scalable video processing.

## ✨ Features

- 🎥 **YouTube Video Download**: Download individual videos or entire channels using yt-dlp
- 🎤 **AI Transcription**: CPU-optimized OpenAI Whisper transcription (no GPU required)
- 🚀 **Async Processing**: Celery-based queue system for concurrent downloads and transcriptions
- 🐳 **Docker Ready**: Complete Docker setup with optimized build times (~2 minutes)
- 🌐 **Web Interface**: Next.js frontend for easy interaction
- 📊 **Monitoring**: Flower dashboard for queue monitoring
- 🔄 **Auto-Processing**: Automatic transcription of downloaded videos

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Redis         │
│   (Next.js)     │◄──►│   API Server    │◄──►│   Queue Broker  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Celery Download │ │ Celery Transc.  │ │ Flower Monitor  │
    │ Worker          │ │ Worker          │ │ Port: 5556      │
    │ (yt-dlp)        │ │ (Whisper)       │ │                 │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM (for Whisper model loading)

### 1. Clone and Start

```bash
git clone https://github.com/yourusername/queuetube-whisper-transcriber.git
cd queuetube-whisper-transcriber
docker compose up --build
```

### 2. Access Services

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Queue Monitor**: http://localhost:5556

## 🧪 Testing Commands

### Download a Single Video

```bash
# Download a specific YouTube video
curl -X POST "http://localhost:8000/download_url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Process All Downloaded Videos for Transcription

```bash
# Trigger transcription of all untranscribed videos
curl -X POST "http://localhost:8000/process_untranscribed_videos"
```

### Check Download Status

```bash
# Monitor download worker logs
docker compose logs celery_download --follow --tail=20

# Monitor transcription worker logs
docker compose logs celery_transcription --follow --tail=20
```

### List Downloaded Files

```bash
# See what's been downloaded
docker compose exec api find downloads -name "*.mp4" -o -name "*.txt" | head -10
```

### Test API Health

```bash
# Check if API is running
curl http://localhost:8000/health

# Get API documentation
curl http://localhost:8000/docs
```

## 📁 Project Structure

```
queuetube-whisper-transcriber/
├── app/                          # Backend Python application
│   ├── api.py                   # FastAPI routes and endpoints
│   ├── audio_tools.py           # Audio processing utilities
│   ├── download_processor.py    # YouTube download Celery tasks
│   ├── transcription_processor.py # Whisper transcription tasks
│   └── whisper_transcriber.py   # OpenAI Whisper integration
├── frontend/                     # Next.js frontend
│   ├── pages/
│   │   ├── index.js            # Main frontend page
│   │   └── index.module.css    # Styling
│   └── package.json            # Frontend dependencies
├── downloads/                    # Downloaded videos and transcripts
├── models/                      # Whisper model cache
├── docker-compose.yml           # Multi-service Docker setup
├── Dockerfile                   # Optimized Python container
└── pyproject.toml              # Python dependencies
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Customize Redis connection
REDIS_URL=redis://redis:6379/0

# Optional: Change Whisper model size
WHISPER_MODEL=tiny.en  # Options: tiny.en, base.en, small.en, medium.en, large
```

### Whisper Models

The system uses OpenAI Whisper models. Available options:

- `tiny.en` (39 MB) - Fastest, good for testing
- `base.en` (142 MB) - Good balance of speed/accuracy
- `small.en` (488 MB) - Better accuracy
- `medium.en` (1.5 GB) - High accuracy
- `large` (3 GB) - Best accuracy, multilingual

## 🐳 Docker Services

| Service                | Description          | Port | Purpose                     |
| ---------------------- | -------------------- | ---- | --------------------------- |
| `api`                  | FastAPI server       | 8000 | REST API endpoints          |
| `redis`                | Redis broker         | 6379 | Task queue storage          |
| `celery_download`      | Download worker      | -    | YouTube video downloading   |
| `celery_transcription` | Transcription worker | -    | Whisper audio transcription |
| `flower`               | Queue monitor        | 5556 | Celery task monitoring      |
| `frontend`             | Next.js app          | 3000 | Web interface               |

## 📊 Monitoring

### View Queue Status

Visit http://localhost:5556 to see:

- Active/pending tasks
- Worker status
- Task history
- Performance metrics

### Check Logs

```bash
# All services
docker compose logs --follow

# Specific service
docker compose logs celery_download --follow
docker compose logs celery_transcription --follow
docker compose logs api --follow
```

## 🔍 API Endpoints

### Core Endpoints

| Method | Endpoint                        | Description                      | Example                                      |
| ------ | ------------------------------- | -------------------------------- | -------------------------------------------- |
| `POST` | `/download_url`                 | Download a YouTube video         | `{"url": "https://youtube.com/watch?v=..."}` |
| `POST` | `/process_untranscribed_videos` | Transcribe all downloaded videos | -                                            |
| `GET`  | `/health`                       | API health check                 | -                                            |
| `GET`  | `/docs`                         | Interactive API documentation    | -                                            |

### Example API Usage

```bash
# Download a video
curl -X POST "http://localhost:8000/download_url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VYr3rMJfPFc"}'

# Start transcription process
curl -X POST "http://localhost:8000/process_untranscribed_videos"

# Check API health
curl http://localhost:8000/health
```

## 🛠️ Development

### Local Development Setup

```bash
# Install dependencies
poetry install

# Run tests (if available)
pytest

# Format code
black app/
isort app/

# Type checking
mypy app/
```

### Rebuilding Services

```bash
# Rebuild specific service
docker compose build celery_download
docker compose up -d celery_download

# Rebuild all services
docker compose build --no-cache
docker compose up -d
```

## 🚨 Troubleshooting

### Common Issues

**Build takes too long (>20 minutes)**

- The optimized Dockerfile should build in ~2 minutes
- If slow, check Docker resources and internet connection

**Download fails with 403 Forbidden**

- YouTube anti-bot measures
- Try different video or wait and retry
- Check yt-dlp version is latest

**Transcription worker crashes**

- Check available RAM (needs 2-4GB)
- Try smaller Whisper model (`tiny.en`)
- Monitor logs: `docker compose logs celery_transcription`

**Frontend won't start**

- Ensure Node.js image has yarn enabled
- Check frontend logs: `docker compose logs frontend`

### Debug Commands

```bash
# Check service status
docker compose ps

# Restart specific service
docker compose restart celery_download

# View resource usage
docker stats

# Clean up
docker compose down
docker system prune -f
```

## 📈 Performance Tips

1. **CPU Optimization**: Uses CPU-only PyTorch for better Docker compatibility
2. **Model Caching**: Whisper models are cached in `./models/` volume
3. **Concurrent Processing**: Separate workers for download and transcription
4. **Memory Management**: Optimized for 4GB+ RAM systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test with provided commands
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Celery](https://docs.celeryproject.org/) for task queuing

---

**Ready to transcribe?** 🎉 Start with `docker compose up --build` and visit http://localhost:3000!
