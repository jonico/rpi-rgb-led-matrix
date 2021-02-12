import subprocess

class Pod:
     def __init__(self, podName, podStatus, podNode, position):
         self.podName = podName
         self.podStatus = podStatus
         self.podNode = podNode
         self.position = position

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
        'Completed': 'grey',
        'Pending': 'yellow'
    }.get(status, 'white')

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

podsSeenThisRound = set()
podsToBeInsertedThisRound = []

output = subprocess.check_output("kubectl get pods --namespace actions-runner-link --no-headers -o wide", shell=True)
for row in output.split('\n'):
    values = row.split();
    if (not values):
        continue
    podName = values[0]
    podStatus = values[2]
    nodeName = values[6]

    if (nodeName not in nodes.keys()):
        continue

    podsSeenThisRound.add(podName)

    pod = nodes.get(nodeName).get(podName)
    if (not pod):
        # we have to schedule the position after this lopp
        podsToBeInsertedThisRound.append(Pod(podName, podStatus, nodeName, -1))
    else:
        # we only change the status, position is already set
        nodes[nodeName][podName] = Pod(podName, podStatus, nodeName, pod.position)

performedDefrag = False
for pod in podsToBeInsertedThisRound:
    position = find_first_unused_position(positionsAlreadyTaken[pod.podNode])
    if position >= positionMax:
        if not performedDefrag:
            # idea: turn defrag logic into a function
            for node, existingPods in nodes.items():
                for podName, existingPod in existingPods.items():
                    if (not podName in podsSeenThisRound):
                        # mark position for potential override, don't do it yet
                        positionsAlreadyTaken[existingPod.podNode].remove(existingPod.position)
            performedDefrag = True
        position = find_first_unused_position(positionsAlreadyTaken[pod.podNode])

    pod.position = position
    positionsAlreadyTaken[pod.podNode].add(position)
    nodes[pod.podNode][pod.podName] = pod
    if (position<len(nodesByPosition[pod.podNode])):
        previousPod = nodesByPosition[pod.podNode][pod.position]
        nodes[previousPod.podNode].pop(previousPod.podName)
        nodesByPosition[pod.podNode][pod.position]=pod
    else:
        nodesByPosition[pod.podNode].append(pod)


offsetX = 0
for node, pods in nodesByPosition.items():
    i = 0
    for pod in pods:
        print("Pod: %s, Status: %s, Node: %s, Color: %s, Position: %i" % (pod.podName, pod.podStatus, pod.podNode, status_color(pod.podStatus), pod.position))
        basePosX = (i * podPixelLength) % maxX
        print "BasePos: %d" % basePosX
        basePosY = (int) (i*podPixelLength/maxX) * podPixelHeight
        for x in range (0, podPixelLength):
            for y in range (0, podPixelHeight):
                print("x: %d, y: %d, color: %s" % (basePosX + offsetX + x, basePosY + y, status_color(pod.podStatus)))
        i+=1
    offsetX += maxX
