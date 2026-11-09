import os

from setuptools import setup


package_name = 'atlas_person_2'

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml', 'README.md']),
]

for directory in ('config', 'launch', 'models', 'worlds'):
    for root, subdirectories, files in os.walk(directory):
        subdirectories[:] = [
            subdirectory for subdirectory in subdirectories
            if subdirectory != '__pycache__'
        ]
        files = [filename for filename in files if not filename.endswith('.pyc')]
        if files:
            data_files.append((
                os.path.join('share', package_name, root),
                [os.path.join(root, filename) for filename in files],
            ))

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    package_dir={package_name: package_name},
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='A.T.L.A.S Person 2',
    maintainer_email='dhruv@example.com',
    description='Independent A.T.L.A.S Gazebo Harmonic missions.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'mission_2_goal = atlas_person_2.mission_2_goal:main',
            'mission_3_goal = atlas_person_2.mission_3_goal:main',
            'dynamic_obstacle = atlas_person_2.dynamic_obstacle:main',
        ],
    },
)
