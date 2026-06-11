from setuptools import setup, find_packages
setup(
    name="sorabbyngo-hal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["psutil>=5.9.0", "nats-py>=2.6.0", "requests>=2.31.0"],
)
