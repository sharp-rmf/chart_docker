
# Copyright 2021 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import rclpy
import math
import argparse
import yaml
import time
from rclpy.node import Node
from rclpy.time import Time

from rclpy.qos import qos_profile_system_default
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy as History
from rclpy.qos import QoSDurabilityPolicy as Durability
from rclpy.qos import QoSReliabilityPolicy as Reliability

from rmf_fleet_msgs.msg import ModeRequest, PathRequest, Location, \
    RobotState, RobotMode, DockSummary, Dock, DockParameter


def make_location(p, level_name):
    location = Location()
    location.x = p[0]
    location.y = p[1]
    location.yaw = p[2]
    location.level_name = level_name
    return location


def close(self, l0: Location, l1: Location):
    x_2 = (l1.x - l0.x) ** 2
    y_2 = (l1.y - l0.y) ** 2
    dist = math.sqrt(x_2 + y_2)

    f_x = l0.x
    f_y = l0.y
        
    c_x = l1.x
    c_y = l1.y

    self.get_logger().info(
      f'Is bot close to: {f_x}, {f_y}? -> {c_x}, {c_y}')
    
    if dist > 0.2:
        return False
    return True


class MockDocker(Node):
    """
    This Mock Docker provides the fleet adapter a series of prerecorded docking
    path for the robot to follow during "Dock Mode". Internally, a dock_summary
    will get sent to the fleet adapter for initial clean task estimation.
    Also, during the docking process. The mock_docker will response to a valid
    Docking Mode Request from the fleet adapter, followed by sending a
    fix dock path request to the underlying fleet driver or slotcar.

    Althought this is named as Docking. this process can also be used to mimic
    a cleaning robot, which is following a known path during cleaning.
    """

    def __init__(self, config_yaml):
        super().__init__('mock_docker')
        print(f"Greetings, I am mock docker")
        self.config_yaml = config_yaml 

        self.mode_request_subscription = self.create_subscription(
            ModeRequest, 'robot_mode_requests', self.mode_request_cb, 10)

        self.robot_state_subscription = self.create_subscription(
            RobotState, 'robot_state', self.robot_state_cb, 10)

        transient_qos = QoSProfile(
            history=History.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1,
            reliability=Reliability.RMW_QOS_POLICY_RELIABILITY_RELIABLE,
            durability=Durability.RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL)
        self.dock_summary_publisher = self.create_publisher(
            DockSummary, 'dock_summary', qos_profile=transient_qos)

        # This is a dict of robots which are in docking m .items():
                param = DockParameter()
                param.start = dock_name
                # TODO This is a hack. The cleaning task will ensure the
                # robot ends up at the finish waypoint. The graph already
                # containts these waypoints
                param.finish = param.start + "_start"
                for point in dock_waypoints["path"]:
                    location = make_location(
                        point, dock_waypoints["level_name"])
                    param.path.append(location)
                dock.params.append(param)
                dock_sub_map[dock_name] = param.path
            dock_summary.docks.append(dock)
            self.dock_map[fleet_name] = dock_sub_map
        self.dock_summary_publisher.publish(dock_summary)

    def mode_request_cb(self, msg: ModeRequest):
        if msg.mode.mode != RobotMode.MODE_DOCKING:
            return

        if not msg.parameters:
            print(f'Missing docking name for docking request!')
            return

        if msg.parameters[0].name != 'docking':
            print(f'Unexpected docking parameter [{msg.parameters[0]}]')
            return

        fleet_name = self.dock_map.get(msg.fleet_name)
        if fleet_name is None:
            print('Unknown fleet name reuested [{msg.fleet_name}].')
            return

        dock = fleet_name.get(msg.parameters[0].value)
        if not dock:
            print(f'Unknown dock name requested [{msg.parameters[0].value}]')
            return

        self.get_logger().info(f'Docking mode request recieved, placing robot into watch: watching[{msg.robot_name}]=path_request')

        path_request = PathRequest()
        path_request.fleet_name = msg.fleet_name
        path_request.robot_name = msg.robot_name
        path_request.task_id = msg.task_id
        path_request.path = dock
        self.watching[msg.robot_name] = path_request

        # self.path_request_publisher.publish(path_request)

    def robot_state_cb(self, msg: RobotState):
        robot_name = msg.name
        if robot_name not in self.watching:
            return

        requested_path = self.watching[msg.name]
        finish_location = requested_path.path[-1]

        if not close(self, finish_location, msg.location):
            return
        

        # This is needed to acknowledge the slot car that a Docking Mode
        # is completed. Subsequently, this will update the robot_state and
        # inform the Fleet adapter that the robot has fnished docking
        mode_request = ModeRequest()
        mode_request.fleet_name = requested_path.fleet_name
        mode_request.robot_name = requested_path.robot_name
        mode_request.task_id = requested_path.task_id
        mode_request.mode.mode = RobotMode.MODE_PAUSED
        self.mode_request_publisher.publish(mode_request)

        # Remove from watching, when it is no longer in Docking
        if msg.mode.mode != RobotMode.MODE_DOCKING:
            self.watching.pop(robot_name)
            self.get_logger().info(
                f'{robot_name} done with docking at {finish_location}')


def main(argv=sys.argv):
    rclpy.init(args=argv)
    args_without_ros = rclpy.utilities.remove_ros_args(argv)
    parser = argparse.ArgumentParser(
        prog="mock_docker",
        description="Configure and start mock_docker node")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Path to config file")
    args = parser.parse_args(args_without_ros[1:])

    config = args.config

    with open(config, "r") as f:
        config_yaml = yaml.safe_load(f)

    mock_docker = MockDocker(config_yaml)
    rclpy.spin(mock_docker)
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
