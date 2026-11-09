#!/usr/bin/env bash
# Usage: person_2/scripts/run_mission.sh <2|3> [extra ros2 launch args...]
# Stops stale simulation processes, then launches the chosen mission.
set -e
mission="${1:?usage: run_mission.sh <2|3> [launch args]}"
shift || true
ws="$(cd "$(dirname "$0")/../.." && pwd)"

for p in "gz sim" component_container slam_toolbox parameter_bridge \
         robot_state_publisher lifecycle_manager map_saver_server \
         mission_._goal dynamic_obstacle; do
  pkill -f "$p" 2>/dev/null || true
done
sleep 2

source /opt/ros/jazzy/setup.bash
source "$ws/install/setup.bash"
exec ros2 launch atlas_person_2 "mission_${mission}.launch.py" "$@"
