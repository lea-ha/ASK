#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Ask App...${NC}"

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill 0
}
trap cleanup EXIT

# Start backend
echo -e "${GREEN}📡 Starting backend server...${NC}"
cd ask-backend
if [ -d "ask/Scripts" ]; then
    source ask/Scripts/activate
else
    echo -e "${RED}Virtual environment not found. Creating one...${NC}"
    python -m venv ask
    source ask/Scripts/activate
    pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt found"
fi

python api.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}🎨 Starting frontend server...${NC}"
cd ../ask-frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

npm start &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Both servers started!${NC}"
echo -e "${YELLOW}Backend: http://localhost:5000${NC}"
echo -e "${YELLOW}Frontend: http://localhost:3000${NC}"

# Wait for both processes
wait