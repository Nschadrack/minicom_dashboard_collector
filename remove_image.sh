# Recreate the directory with proper permissions
mkdir ../postgres_data && sudo chown -R 1001:1001 ../postgres_data
sudo chown 999:999 ../postgres_data

# Stop and remove ALL containers/volumes from previous setups
docker compose down --remove-orphans --volumes --rmi all

# Function to kill process running on a given port
kill_port_process() {
  local PORT=$1
  PID=$(lsof -ti tcp:$PORT)

  if [ -n "$PID" ]; then
    echo "Process found on port $PORT: PID $PID"
    echo "Killing process..."
    kill -9 $PID
    echo "Process on port $PORT killed."
  else
    echo "No process is running on port $PORT."
  fi
}

# Check and kill for port 80
kill_port_process 80

# Check and kill for port 443
kill_port_process 443