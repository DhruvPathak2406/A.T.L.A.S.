#!/usr/bin/env bash
# Usage: person_1/scripts/run_mission.sh [extra ros2 launch args...]
# Stops stale simulation processes, then launches Mission 1 (Rubble Run).
set -e
ws="$(cd "$(dirname "$0")/../.." && pwd)"

for p in "gz sim" component_container slam_toolbox parameter_bridge \
         robot_state_publisher lifecycle_manager map_saver_server \
         mission_1_goal; do
  pkill -f "$p" 2>/dev/null || true
done
sleep 2

source /opt/ros/jazzy/setup.bash
source "$ws/install/setup.bash"
exec ros2 launch atlas_person_1 mission_1.launch.py "$@"
