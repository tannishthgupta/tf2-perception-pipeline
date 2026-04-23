import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from scipy.spatial.transform import Rotation as R
from tf2_ros import TransformBroadcaster
import math
import time

class Broadcaster(Node):
    def __init__(self):
        super().__init__('tf_broadcaster')

        self.br = TransformBroadcaster(self)
        self.timer = self.create_timer(0.1, self.broadcast)

        
        self.start_time = time.time()

    def broadcast(self):
        t = time.time() - self.start_time

        # Circular motion
        x = 2 * math.cos(t)
        y = 2 * math.sin(t)
        theta = t

        # world → base_link
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = 'world'
        transform.child_frame_id = 'base_link'

        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = 0.0

        q = R.from_euler('z', theta).as_quat()

        transform.transform.rotation.x = q[0]
        transform.transform.rotation.y = q[1]
        transform.transform.rotation.z = q[2]
        transform.transform.rotation.w = q[3]

        self.br.sendTransform(transform)

        # base_link → sensor_frame (fixed offset)
        sensor = TransformStamped()
        sensor.header.stamp = self.get_clock().now().to_msg()
        sensor.header.frame_id = 'base_link'
        sensor.child_frame_id = 'sensor_frame'

        sensor.transform.translation.x = 0.5
        sensor.transform.translation.y = 0.0
        sensor.transform.translation.z = 0.0

        sensor.transform.rotation.w = 1.0

        self.br.sendTransform(sensor)


def main():
    rclpy.init()
    node = Broadcaster()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
