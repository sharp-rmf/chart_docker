FROM ghcr.io/open-rmf/rmf/rmf_demos:latest
LABEL ghcr.io/open-rmf/rmf/rmf_demos:latest rmf:latest

RUN  apt-get update \
  && apt-get install -y ros-galactic-rmw-cyclonedds-cpp \
    python3-vcstool \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /magni_ws/src/
COPY chart.repos /magni_ws/src/chart.repo
# RUN vcs import src < magni

# ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# RUN . /opt/ros/$ROS_DISTRO/setup.bash 
# export ROS_DOMAIN_ID=9; ros2 launch rmf_demos_gz office.launch.xml headless:=1"