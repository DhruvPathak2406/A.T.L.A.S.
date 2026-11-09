# A.T.L.A.S Person 2 missions

This package contains two independent Gazebo Harmonic missions using the
installed Jazzy TurtleBot3 Waffle simulation model. Its existing Gazebo
description provides differential drive, `/scan`, `/odom`, and `odom` to
`base_footprint` TF; the supplied bridge and robot-state publisher expose those
interfaces to Nav2.

## Build and launch

From the workspace root:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths person_2 --ignore-src -r -y
colcon build --base-paths person_2 --packages-select atlas_person_2
source install/setup.bash
```

Run one mission at a time (the helper script first kills stale Gazebo/Nav2
processes, which otherwise break the next run):

```bash
./person_2/scripts/run_mission.sh 2   # hostile corridor: (-7,-4.5) -> (+14.2,+8.6)
./person_2/scripts/run_mission.sh 3   # counter threat:   (-8,-5)   -> (+16,+10), moving hazard
```

Equivalent direct commands (kill stale processes yourself first):

```bash
ros2 launch atlas_person_2 mission_2.launch.py
ros2 launch atlas_person_2 mission_3.launch.py
```

The Gazebo GUI opens by default; pass `headless:=true` for server-only
rendering. Mission 3 accepts configurable hazard
motion, for example:

```bash
ros2 launch atlas_person_2 mission_3.launch.py \
  hazard_speed:=0.30 \
  hazard_waypoints:='-0.2,-1.7;-0.2,1.7;0.4,1.7;0.4,-1.7'
```

The first waypoint must match the hazard's initial pose in
`worlds/counter_threat.sdf`; points are world-frame x,y pairs. Speed is limited
to 0.05–0.5 m/s.

## Navigation and verification

Each mission launches online SLAM, Nav2, a 10 Hz scan-updated local obstacle
costmap, a rolling global obstacle costmap, and the mission's
`NavigateToPose` client. The Nav2 behavior tree replans the global path while
the MPPI controller samples candidate trajectories against live costmap
obstacles.
Mission 3's red mobile hazard is a Gazebo differential-drive model; its
collision and visual bodies intersect the Waffle's LiDAR scan plane, and the
`dynamic_obstacle` ROS node drives its `/hazard/cmd_vel` topic through
`ros_gz_bridge`.

The SLAM map origin is initialized at the deployment pose (map x=0, y=0), so
the goal coordinates are the displacement from deployment to the secured or
extraction zone. To check the live interfaces:

```bash
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo map base_footprint
ros2 action list | grep navigate_to_pose
```
