FROM ghcr.io/open-rmf/rmf/rmf_demos:latest
LABEL ghcr.io/open-rmf/rmf/rmf_demos:latest rmf:latest

# FROM ros:galactic-ros-base

# RUN  apt update &&\
#   apt install -y wget &&\
#   sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list' &&\
#   wget https://packages.osrfoundation.org/gazebo.key -O - | apt-key add - &&\
#   apt install -y ros-galactic-rmf-demos-gz

RUN  apt-get update \
  && apt-get install -y ros-foxy-rmw-cyclonedds-cpp \
    python3-vcstool \
  && rm -rf /var/lib/apt/lists/*

# RUN  apt-get update \
#   && apt-get install -y python3-vcstool \
#   && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /magni_ws/src
WORKDIR /magni_ws 
RUN wget https://raw.githubusercontent.com/sharp-rmf/chart_docker/main/chart.repos
RUN vcs import src < chart.repos

RUN apt-get update && \
    rosdep update && \
    rosdep install -y \
      --from-paths \
        src \
      --ignore-src -r

# RUN /bin/bash -c '. /opt/ros/$ROS_DISTRO/setup.bash' && colcon build --symlink-install; colcon build --symlink-install
# RUN /bin/bash -c '. /opt/ros/$ROS_DISTRO/setup.bash' && colcon build
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# RUN . /opt/ros/$ROS_DISTRO/setup.bash 
# export ROS_DOMAIN_ID=9; ros2 launch rmf_demos_gz office.launch.xml headless:=1"