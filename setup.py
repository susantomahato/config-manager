"""Setup configuration for config-manager."""

from setuptools import setup

setup(
    name='config-manager',
    version='1.0.0',
    author='Susanto Mahato',
    description='A YAML-based configuration management system',
    url='https://github.com/susantomahato/config-manager',
    py_modules=['config_manager', 'sync_service', 'constants'],
    package_dir={'': 'src'},
    python_requires='>=3.6',
    install_requires=[
        'PyYAML>=5.3.1',
        'GitPython>=3.1.0',
        'click>=7.0',
    ],
    entry_points={
        'console_scripts': [
            'config-manager=config_manager:main',
            'config-sync=sync_service:main',
        ],
    },
)
