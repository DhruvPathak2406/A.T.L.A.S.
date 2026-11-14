# A.T.L.A.S Person 1: Mission 1 (Rubble Run)

This package contains the independent Gazebo Harmonic Mission 1 (Rubble Run) simulation for the A.T.L.A.S project using ROS 2 Jazzy Jalisco and the TurtleBot3 Waffle simulation model.

The mission tasks the robot with deploying into an urban rubble and debris field, exploring and mapping the unknown environment with online SLAM (`slam_toolbox`), and navigating through multiple choke points and collapsed concrete obstacles to safely reach the designated extraction zone.

---

## Mission Specifications

- **Simulator**: Gazebo Harmonic (`gz sim` via `ros_gz_sim`)
- **Robot Model**: TurtleBot3 Waffle (`nav2_minimal_tb3_sim`)
- **World**: `worlds/rubble_run.sdf`
- **Deployment (Start) Pose**: `x = -6.5`, `y = -3.5`, `z = 0.01`, `yaw = 0.0 rad`
- **Extraction (Goal) Pose (World)**: `x = 6.5`, `y = 3.5`, `yaw = 0.0 rad`
- **Goal Displacement in Map (SLAM)**: `goal_x = 13.0`, `goal_y = 7.0`, `goal_yaw = 0.0`
- **Controller**: Nav2 MPPI Controller (`nav2_mppi_controller::MPPIController`) with DiffDrive motion model
- **Planner**: Navfn Planner (`nav2_navfn_planner::NavfnPlanner`) with A* search
- **Perception**: 2D LiDAR (`/scan`) feeding a 10 Hz local costmap and rolling global costmap with tuned inflation for narrow rubble passages.

---

## Build and Setup

From the workspace root (`ATLAS/Scenario 1/`):

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths person_1 --ignore-src -r -y
colcon build --base-paths person_1 --packages-select atlas_person_1
source install/setup.bash
```

---

## Launching Mission 1

### Helper Script (Recommended)
Kills any stale Gazebo/Nav2 processes before launching to ensure clean execution:

```bash
./person_1/scripts/run_mission.sh
```

### Direct ROS 2 Launch
```bash
ros2 launch atlas_person_1 mission_1.launch.py
```

### Headless Simulation (No GUI)
For headless systems or CI/automated runs:
```bash
ros2 launch atlas_person_1 mission_1.launch.py headless:=true
```

---

## ROS 2 Topics and Interfaces

| Topic / Action | Type | Direction / Purpose |
| :--- | :--- | :--- |
| `/clock` | `rosgraph_msgs/msg/Clock` | GZ $\rightarrow$ ROS simulation time synchronization |
| `/scan` | `sensor_msgs/msg/LaserScan` | GZ $\rightarrow$ ROS 2D LiDAR sensor scans |
| `/odom` | `nav_msgs/msg/Odometry` | GZ $\rightarrow$ ROS wheel odometry |
| `/tf` | `tf2_msgs/msg/TFMessage` | GZ $\rightarrow$ ROS dynamic transforms (`odom` $\rightarrow$ `base_footprint`) |
| `/joint_states` | `sensor_msgs/msg/JointState` | GZ $\rightarrow$ ROS joint state monitoring |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS $\rightarrow$ GZ velocity drive commands |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Nav2 action server for mission goal execution |

To verify active topics during simulation:
```bash
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo map base_footprint
ros2 action list | grep navigate_to_pose
```
