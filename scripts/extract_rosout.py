import argparse
import os
import sys
import rclpy
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def map_level_to_txt(level):
    level_map = {10: "DEBUG", 20: "INFO", 30: "WARN", 40: "ERROR", 50: "FATAL"}
    return level_map.get(level, "UNKNOWN")


def format_msg(msg):
    return f"[{msg.stamp.sec}.{msg.stamp.nanosec}] {map_level_to_txt(msg.level)}: {msg.name} - {msg.msg}"


def extract_logs(args):

    bag_reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(
        uri=args["ros_bag"], storage_id=args["storage_id"]
    )
    converter_options = rosbag2_py.ConverterOptions("", "")
    bag_reader.open(storage_options, converter_options)

    type_map = {t.name: t.type for t in bag_reader.get_all_topics_and_types()}
    msg_type = get_message(type_map[args["tos_topic"]])  # rcl_interfaces/msg/Log

    output_file = args["output"]
    with open(output_file, "w") as f:
        while bag_reader.has_next():
            (topic, data, t) = bag_reader.read_next()
            if topic == args["tos_topic"]:
                msg = deserialize_message(data, msg_type)
                msg = format_msg(msg)
                f.write(str(msg) + "\n")


if __name__ == "__main__":
    # Argparse
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-b",
        "--ros_bag",
        required=True,
        type=str,
        help="Path to ROSBAG to be extracted.",
    )
    ap.add_argument(
        "-t",
        "--tos_topic",
        required=False,
        type=str,
        default="/rosout",
        help="Name of ros2 topic that record the logs. Must have the same format as /rosout.",
    )
    ap.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        default="extracted_logs.txt",
        help="Path to the output file where extracted logs will be saved.",
    )
    ap.add_argument(
        "-i",
        "--storage-id",
        required=False,
        type=str,
        default="mcap",
        help="Storage ID for the ROS bag (e.g., sqlite3, memory, mcap). Mcap is default.",
    )

    args = vars(ap.parse_args())

    # Check that path exists
    if not os.path.exists(args["ros_bag"]):
        raise FileNotFoundError(f"ROS bag not found: {args['ros_bag']}")
        sys.exit(1)

    extract_logs(args)
