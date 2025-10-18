# === CONFIG ===
REPO_URL="https://github.com/nathanengineer/project_naari.git"
APP_NAME="naari"
DEFAULT_PORT=80
BRANCH="${1:-main}"
ENV_FILE=".env"
CONFIG_FILE="$(pwd)/naari_config.json"

# === STEP 1: Detect if already inside repo ===
if [ -d ".git" ]; then
  echo "📂 Already inside Git repo — checking out latest $BRANCH..."
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  echo "📦 Checking for cloned repo..."
  if [ ! -d "$APP_NAME" ]; then
    echo "🌱 Cloning branch $BRANCH from $REPO_URL into $APP_NAME/"
    git clone -b "$BRANCH" "$REPO_URL" "$APP_NAME"
  fi

  cd "$APP_NAME" || {
    echo "❌ Failed to enter $APP_NAME directory."
    exit 1
  }
fi

# === STEP 2: Load environment variables (optional) ===
if [ -f "$ENV_FILE" ]; then
  echo "📄 Loading settings from $ENV_FILE"
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "⚠️  No .env file found — using defaults and prompt where needed."
fi

# Mount Config File if exists
if [ -f "$CONFIG_FILE" ]; then
  CONFIG_MOUNT="-v $CONFIG_FILE:/app/naari_config.json"
else
  echo "⚠️  No config file found. Container will create it."
  CONFIG_MOUNT=""
fi

# === STEP 3: Determine networking mode ===
USE_MACVLAN="${USE_MACVLAN:-0}"         # Set to 1 in .env to use macvlan
DOCKER_NET_NAME="${DOCKER_NET_NAME:-}"  # e.g., pi-macnet
CONTAINER_IP="${CONTAINER_IP:-}"

# Prompt only if macvlan is being used and values are missing
if [[ "$USE_MACVLAN" == "1" ]]; then
  [[ -z "$DOCKER_NET_NAME" ]] && read -rp "Enter Docker macvlan network name (e.g. pi-macnet): " DOCKER_NET_NAME
  [[ -z "$CONTAINER_IP" ]] && read -rp "Enter container IP (e.g. 192.168.1.201): " CONTAINER_IP
fi

#Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    docker rmi $CONTAINER_NAME
fi

# === STEP 4: Build Docker image ===
echo "🐳 Building Docker image..."
docker build -t "$APP_NAME" .

# === STEP 5: Run container ===
echo "🚀 Running container..."

if [[ "$USE_MACVLAN" == "1" ]]; then
  docker run -d \
    --name "$APP_NAME" \
    --network "$DOCKER_NET_NAME" \
    --ip "$CONTAINER_IP" \
    --env-file "$ENV_FILE" \
    $CONFIG_MOUNT \
    "$APP_NAME"
else
  docker run -d \
    --name "$APP_NAME" \
    --network host \
    --env-file "$ENV_FILE" \
    $CONFIG_MOUNT \
    "$APP_NAME"
fi
