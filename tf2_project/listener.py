import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
from tf2_ros import Buffer, TransformListener
import tf2_geometry_msgs
import math
from visualization_msgs.msg import Marker
import random

class Listener(Node):
    def __init__(self):
        super().__init__('tf_listener')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.obstacles = [
            # ✅ SHOULD BE DETECTED (x > 0 and within 3m)
            (1.0, 0.5),
            (2.0, 1.0),
            (2.5, -1.0),
            (1.5, -0.5),
            (0.8, 2.0),
            (2.2, 0.2),
            (1.2, -2.2),

            # ❌ OUT OF RANGE (> 3m)
            (3.5, 0.0),
            (4.0, 1.0),
            (3.2, -2.5),

            # ❌ BEHIND ROBOT (x < 0)
            (-1.0, 0.5),
            (-2.0, -1.0),
            (-0.5, 2.0),
            (-3.0, 0.0),

            # ❌ EDGE CASE (just outside range or borderline)
            (3.01, 0.1)
        ]
        self.publisher_ = self.create_publisher(PointStamped, 'world_point', 10)
        self.marker_pub = self.create_publisher(Marker, 'lidar_points', 10)
        self.timer = self.create_timer(1.0, self.lookup)



    def lookup(self):
        try:
            
            from rclpy.time import Time

            sensor_points = []

            # WORLD → SENSOR (simulate what robot sees)
            for (x, y) in self.obstacles:
                p = PointStamped()
                p.header.frame_id = 'world'
                p.header.stamp = Time().to_msg()

                p.point.x = x
                p.point.y = y
                p.point.z = 0.0

                try:
                    sp = self.tf_buffer.transform(p, 'sensor_frame')
                    noise = 0.1  # start with 10 cm

                    sp.point.x += random.uniform(-noise, noise)
                    sp.point.y += random.uniform(-noise, noise)
                    if sp.point.x > 0:  # only front-facing
                        sensor_points.append(sp)

                        dist = math.sqrt(sp.point.x**2 + sp.point.y**2)

                        if dist < 3.0:
                            sensor_points.append(sp)

                except Exception as e:
                    self.get_logger().warn(f"World→Sensor failed: {e}")


            # SENSOR → WORLD (reconstruction)
            world_points = []

            for sp in sensor_points:
                try:
                    wp = self.tf_buffer.transform(sp, 'world')
                    world_points.append(wp)
                except Exception as e:
                    self.get_logger().warn(f"Sensor→World failed: {e}")


            marker = Marker()
            marker.header.frame_id = 'world'
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = "lidar"
            marker.id = 0

            marker.type = Marker.POINTS
            marker.action = Marker.ADD

            marker.scale.x = 0.05
            marker.scale.y = 0.05

            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 1.0

            marker.points = []
            # 🔹 Ground Truth Marker (GREEN)
            gt_marker = Marker()
            gt_marker.header.frame_id = 'world'
            gt_marker.header.stamp = self.get_clock().now().to_msg()

            gt_marker.ns = "ground_truth"
            gt_marker.id = 1

            gt_marker.type = Marker.POINTS
            gt_marker.action = Marker.ADD

            gt_marker.scale.x = 0.09
            gt_marker.scale.y = 0.09

            gt_marker.color.r = 0.0
            gt_marker.color.g = 1.0
            gt_marker.color.b = 0.0
            gt_marker.color.a = 1.0

            gt_marker.points = []
            from geometry_msgs.msg import Point

            for (x, y) in self.obstacles:
                pt = Point()
                pt.x = x
                pt.y = y
                pt.z = 0.0
                gt_marker.points.append(pt)

            for wp in world_points:
                marker.points.append(wp.point)

            if world_points:
                sample = world_points[0].point
                self.get_logger().info(
                    f"[LiDAR] Points: {len(world_points)} | Sample: ({sample.x:.2f}, {sample.y:.2f})",
                    throttle_duration_sec=1.0
                )

            self.marker_pub.publish(marker)      # RED (reconstructed)
            self.marker_pub.publish(gt_marker)   # GREEN (ground truth)

        

        except Exception as e:
            self.get_logger().warn(f"Waiting for transform: {str(e)}")


def main():
    rclpy.init()
    node = Listener()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
