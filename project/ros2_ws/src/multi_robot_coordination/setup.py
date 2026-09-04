from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'multi_robot_coordination'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Team 3 Research Group',
    maintainer_email='team3@academic.edu',
    description='Team 3 Project: Multi-Robot Coordination Using ROS 2 Actions and Services',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'coordinator = multi_robot_coordination.multi_robot_coordinator:main',
            'tb3_server = multi_robot_coordination.tb3_action_server:main',
            'ur5_server = multi_robot_coordination.ur5_action_server:main',
            'lock_server = multi_robot_coordination.handoff_service_server:main',
        ],
    },
)
