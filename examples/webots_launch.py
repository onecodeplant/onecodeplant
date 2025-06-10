#!/usr/bin/env python3
"""
Example Webots launch file for OneCodePlant simulator integration.

This launch file demonstrates how to configure Webots with custom worlds
and the ROS2 bridge through the OneCodePlant CLI simulator control system.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for Webots simulation."""
    
    # Declare launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='worlds/empty.wbt',
        description='World file to load in Webots'
    )
    
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='realtime',
        description='Webots execution mode (realtime, fast, pause)'
    )
    
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Set to true for headless mode'
    )
    
    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='robot',
        description='Name of the robot in the world'
    )
    
    # Launch Webots
    webots_launcher = ExecuteProcess(
        cmd=[
            'webots',
            '--mode=' + LaunchConfiguration('mode'),
            LaunchConfiguration('world')
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('headless'))
    )
    
    # Launch Webots with no-rendering for headless
    webots_headless = ExecuteProcess(
        cmd=[
            'webots',
            '--no-rendering',
            '--mode=' + LaunchConfiguration('mode'),
            LaunchConfiguration('world')
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('headless'))
    )
    
    # ROS2 Webots driver
    webots_driver = Node(
        package='webots_ros2_driver',
        executable='driver',
        parameters=[
            {'robot_name': LaunchConfiguration('robot_name')},
            {'use_sim_time': True}
        ],
        output='screen'
    )
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'use_sim_time': True}
        ],
        output='screen'
    )
    
    return LaunchDescription([
        world_arg,
        mode_arg,
        headless_arg,
        robot_name_arg,
        webots_launcher,
        TimerAction(
            period=5.0,  # Wait for Webots to start
            actions=[webots_driver, robot_state_publisher]
        )
    ])