# Configuration Reference

## Config Files Location

- Main: `config/config.yaml`
- Examples: `config/*.yaml.example`

## Main Settings

### Scanner Settings

\`\`\`yaml
scanner:
max_depth: 5 # How deep to scan folders
ignore_patterns: # Patterns to skip - .git - **pycache** - node_modules
file_size_limit_mb: 500 # Max file size to process
\`\`\`

### AI Settings

\`\`\`yaml
ai:
model: "mistral" # Ollama model to use
temperature: 0.7 # 0-1, higher = more creative
max_tokens: 500
timeout_seconds: 30
\`\`\`

### Database Settings

\`\`\`yaml
database:
path: "data/desktop_ai.db"
enable_cache: true
cache_ttl_seconds: 3600
\`\`\`

### Search Settings

\`\`\`yaml
search:
model: "all-minilm" # Embedding model
top_k: 10 # Return top 10 results
similarity_threshold: 0.5 # Min similarity score
faiss_index_type: "flat" # flat or ivf
\`\`\`

### Logging Settings

\`\`\`yaml
logging:
level: INFO # DEBUG, INFO, WARNING, ERROR
file_path: "logs/app.log"
max_size_mb: 10
backup_count: 5
\`\`\`

## Environment Variables

\`\`\`bash
DESKTOPAI_SCAN_FOLDER # Folder to scan
DESKTOPAI_CONFIG_PATH # Custom config location
DESKTOPAI_LOG_LEVEL # Override logging level
DESKTOPAI_DISABLE_OLLAMA # Disable AI features
\`\`\`

## Example Configurations

- [Performance-optimized config]
- [Privacy-focused config]
- [Resource-constrained config]
