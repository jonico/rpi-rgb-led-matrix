#!/usr/bin/env python
from samplebase import SampleBase
import time
import subprocess
from rgbmatrix import graphics

class Pod:
     def __init__(self, name, status, node, position):
         self.name = name
         self.status = status
         self.node = node
         self.position = position


class PodStatusLed(SampleBase):
    def __init__(self, *args, **kwargs):
        super(PodStatusLed, self).__init__(*args, **kwargs)

    def find_first_unused_position (positionSet):
        for i in range (0, 1000):
            if (not i in positionSet):
                 return i
        return 0

    def status_color(status):
      return {
            'Running': 'green',
            'CrashLoopBackOff': 'red',
            'Terminating': 'brown',
            'Completed': 'blue',
            'Pending': 'white',
            'ContainerCreating': 'yellow',
            'Terminated': 'black',
        }.get(status, 'pink')

    def status_color_led(status):
      return {
            'Running': graphics.Color(0, 255, 0),
            'CrashLoopBackOff': graphics.Color(255, 0, 0),
            'CreateContainerError': graphics.Color(255, 0, 0),
            'Terminating': graphics.Color(165,42,42),
            'Completed': graphics.Color(0, 0, 255),
            'Pending': graphics.Color(255, 255, 255),
            'ContainerCreating': graphics.Color(255, 255, 0),
            'Terminated': graphics.Color(0, 0, 0)
        }.get(status, graphics.Color(255,182,193))

    def run(self):
        nodeOne='node64-1'
        nodeTwo='node64-2'

        nodes = { nodeOne : {}, nodeTwo: {} }
        nodesByPosition = { nodeOne: [], nodeTwo: [] }
        positionsAlreadyTaken = {nodeOne: set(), nodeTwo: set() }

        maxX = 32
        maxY = 32
        podPixelLength=8
        podPixelHeight=8
        positionMax = (maxX/podPixelLength)*(maxY/podPixelHeight)

        offscreen_canvas = self.matrix.CreateFrameCanvas()

        while True:
            offscreen_canvas.Clear()
            podsSeenThisRound = set()
            podsToBeInsertedThisRound = []

            output = subprocess.getoutput("kubectl get pods --namespace actions-runner-link --no-headers -o wide")
            for row in output.split("\n"):
                values = row.split();
                if (not values):
                    continue

                podStatus = values[2]
                nodeName = values[6]
                podName = values[0] + "-" + nodeName

                if (nodeName not in nodes.keys()):
                    continue

                podsSeenThisRound.add(podName)

                pod = nodes[nodeName].get(podName)
                if (not pod):
                    # we have to schedule the position after this loop
                    podsToBeInsertedThisRound.append(Pod(podName, podStatus, nodeName, -1))
                else:
                    # we only change the status, and maybe node position is already set
                    pod.status=podStatus

                    #nodesByPosition[pod.node][pod.position]=pod

            performedDefrag = False
            for pod in podsToBeInsertedThisRound:
                position = PodStatusLed.find_first_unused_position(positionsAlreadyTaken[pod.node])
                if position >= positionMax:
                    if not performedDefrag:
                        # idea: turn defrag logic into a function
                        for podName, existingPod in nodes[pod.node].items():
                            if (not podName in podsSeenThisRound):
                                # mark position for potential override, don't do it yet
                                positionsAlreadyTaken[existingPod.node].remove(existingPod.position)
                        performedDefrag = True
                    position = PodStatusLed.find_first_unused_position(positionsAlreadyTaken[pod.node])

                pod.position = position
                positionsAlreadyTaken[pod.node].add(position)
                nodes[pod.node][pod.name] = pod
                if (position<len(nodesByPosition[pod.node])):
                    previousPod = nodesByPosition[pod.node][pod.position]
                    nodes[previousPod.node].pop(previousPod.name)
                    nodesByPosition[pod.node][pod.position]=pod
                else:
                    nodesByPosition[pod.node].append(pod)


            offsetX = 0
            for node, pods in nodesByPosition.items():
                i = 0
                for pod in pods:
                    if (not pod.name in podsSeenThisRound):
                        pod.status="Terminated"
                    print("Pod: %s, Status: %s, Node: %s, Color: %s, Position: %i" % (pod.name, pod.status, pod.node, PodStatusLed.status_color(pod.status), pod.position))
                    basePosX = (i * podPixelLength) % maxX
                    basePosY = (int) (i*podPixelLength/maxX) * podPixelHeight
                    for x in range (0, podPixelLength):
                        for y in range (0, podPixelHeight):
                            # print("x: %d, y: %d, color: %s" % (basePosX + offsetX + x, basePosY + y, PodStatusLed.status_color(pod.status)))
                            color = PodStatusLed.status_color_led(pod.status)
                            # self.matrix.SetPixel(basePosX + offsetX + x, basePosY + y, color.red, color.green, color.blue)
                            offscreen_canvas.SetPixel(basePosX + offsetX + x, basePosY + y, color.red, color.green, color.blue)
                    i+=1
                offsetX += maxX

            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(1)


# Main function
if __name__ == "__main__":
    pod_status_led = PodStatusLed()
    if (not pod_status_led.process()):
        pod_status_led.print_help()
