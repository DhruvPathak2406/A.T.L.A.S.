import os
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import yaml


def _merge_dicts(target, overrides):
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_dicts(target[key], value)
        else:
            target[key] = value
    return target


def _merged_nav2_params(package_share):
    default_params = os.path.join(
        get_package_share_directory('nav2_bringup'), 'params', 'nav2_params.yaml')
    config_dir = os.path.join(package_share, 'config')
    with open(default_params, encoding='utf-8') as stream:
        params = yaml.safe_load(stream)
    for filename in ('nav2_params.yaml', 'local_costmap.yaml', 'controller.yaml'):
        with open(os.path.join(config_dir, filename), encoding='utf-8') as stream:
            _merge_dicts(params, yaml.safe_load(stream))
    path = os.path.join(tempfile.gettempdir(), 'atlas_person_2_nav2_params.yaml')
    with open(path, 'w', encoding='utf-8') as stream:
        yaml.safe_dump(params, stream, sort_keys=False)
    return path


def generate_mission_launch(mission):
    package_share = get_package_share_directory('atlas_person_2')
    tb3_share = get_package_share_directory('nav2_minimal_tb3_sim')
    world_name = 'hostile_corridor' if mission == 2 else 'counter_threat'
    world_file = os.path.join(package_share, 'worlds', world_name + '.sdf')
    bridge_file = os.path.join(package_share, 'config', 'gazebo_bridge.yaml')
    model_dirs = [
        os.path.join(package_share, 'models'),
        os.path.join(package_share, 'models', 'barriers'),
        os.path.join(tb3_share, 'models'),
        os.path.dirname(tb3_share),
    ]
    robot_sdf = os.path.join(tb3_share, 'urdf', 'gz_waffle.sdf.xacro')
    robot_urdf = os.path.join(tb3_share, 'urdf', 'turtlebot3_waffle.urdf')
    nav2_bringup = os.path.join(
        get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')

    start = (-7.0, -4.5, 0.0) if mission == 2 else (-8.0, -5.0, 0.0)
    # SLAM starts each deployment at map (0, 0), while the goal coordinates are
    # expressed as the displacement from that mission's world deployment pose.
    goal = (14.2, 8.6, 0.0) if mission == 2 else (16.0, 10.0, 0.0)
    goal_executable = 'mission_2_goal' if mission == 2 else 'mission_3_goal'

    actions = [
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Set true to run Gazebo without its GUI (rendering sensors stay enabled).'),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(model_dirs)),
    ]

    def configure(context):
        headless = LaunchConfiguration('headless').perform(context).lower() == 'true'
        parameters = _merged_nav2_params(package_share)
        spawn = Node(
            package='ros_gz_sim',
            executable='create',
            name='spawn_atlas',
            output='screen',
            arguments=[
                '-world', world_name,
                '-name', 'atlas',
                '-string', Command([
                    FindExecutable(name='xacro'), ' ', robot_sdf, ' namespace:=',
                ]),
                '-x', str(start[0]), '-y', str(start[1]), '-z', '0.01',
            ],
        )
        return [
            ExecuteProcess(
                cmd=(
                    ['gz', 'sim', '-r', '--headless-rendering', '-s', world_file]
                    if headless else ['gz', 'sim', '-r', world_file]
                ),
                output='screen',
            ),
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name='gazebo_bridge',
                parameters=[{
                    'config_file': bridge_file,
                    'expand_gz_topic_names': False,
                    'use_sim_time': True,
                }],
                output='screen',
            ),
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                parameters=[{
                    'robot_description': open(robot_urdf, encoding='utf-8').read(),
                    'use_sim_time': True,
                }],
                output='screen',
            ),
            spawn,
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_bringup),
                launch_arguments={
                    'slam': 'True',
                    'use_sim_time': 'True',
                    'params_file': parameters,
                    'autostart': 'True',
                }.items(),
            ),
            Node(
                package='atlas_person_2',
                executable=goal_executable,
                name=goal_executable,
                parameters=[{
                    'use_sim_time': True,
                    'goal_x': goal[0],
                    'goal_y': goal[1],
                    'goal_yaw': goal[2],
                }],
                output='screen',
            ),
        ] + ([
            Node(
                package='atlas_person_2',
                executable='dynamic_obstacle',
                name='dynamic_obstacle',
                parameters=[{
                    'use_sim_time': True,
                    'speed': ParameterValue(
                        LaunchConfiguration('hazard_speed'), value_type=float),
                    'waypoints': ParameterValue(
                        LaunchConfiguration('hazard_waypoints'), value_type=str),
                }],
                output='screen',
            ),
        ] if mission == 3 else [])

    if mission == 3:
        actions.extend([
            DeclareLaunchArgument(
                'hazard_speed', default_value='0.22',
                description='Moving hazard speed in metres per second (0.05 to 0.5).'),
            DeclareLaunchArgument(
                'hazard_waypoints',
                default_value='-0.2,-1.7;-0.2,1.7;0.4,1.7;0.4,-1.7',
                description='Semicolon-separated x,y coordinates in the world frame.'),
        ])
    actions.append(OpaqueFunction(function=configure))
    return LaunchDescription(actions)
