#!/usr/bin/env python3
"""
Example Gazebo launch file for OneCodePlant simulator integration.

This launch file demonstrates how to configure Gazebo with custom worlds
and robot models through the OneCodePlant CLI simulator control system.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for Gazebo simulation."""
    
    # Declare launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty_world.sdf',
        description='World file to load in Gazebo'
    )
    
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Set to false for headless mode'
    )
    
    robot_model_arg = DeclareLaunchArgument(
        'robot_model',
        default_value='turtlebot3_burger',
        description='Robot model to spawn'
    )
    
    # Launch Gazebo server
    gazebo_server = ExecuteProcess(
        cmd=['gz', 'sim', '-s', LaunchConfiguration('world')],
        output='screen',
        condition=IfCondition(LaunchConfiguration('gui'))
    )
    
    # Launch Gazebo client (GUI)
    gazebo_client = ExecuteProcess(
        cmd=['gz', 'sim', '-g'],
        output='screen',
        condition=IfCondition(LaunchConfiguration('gui'))
    )
    
    # Spawn robot model
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', LaunchConfiguration('robot_model'),
            '-database', LaunchConfiguration('robot_model'),
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ],
        output='screen'
    )
    
    return LaunchDescription([
        world_arg,
        gui_arg,
        robot_model_arg,
        gazebo_server,
        gazebo_client,
        spawn_robot
    ])