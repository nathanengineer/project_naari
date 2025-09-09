
# === Config ===
REPO_URL="https://github.com/nathanengineer/project_naari.git"
APP_NAME="naari"
APP_PORT=8050
BRANCH="${1:-main}"  # Use first CLI arg as branch, default to 'main'

echo "📦 Cloning $BRANCH branch from $REPO_URL..."

if [ ! -d "$APP_NAME" ]; then
    git clone -b "$BRANCH" "$REPO_URL" "$APP_NAME"
else
    cd "$APP_NAME"
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    cd ..
fi

# === Step 2: Build Docker image ===
echo "🐳 Building Docker image..."
cd "$APP_NAME"
docker build -t "$APP_NAME" .

# === Step 3: Run container ===
echo "🚀 Running Dash app on LAN (port $APP_PORT)..."
docker run --rm --network=host "$APP_NAME"


