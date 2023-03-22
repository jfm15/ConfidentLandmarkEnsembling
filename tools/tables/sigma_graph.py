import numpy as np
import matplotlib.pyplot as plt



ceph_results = np.array([
    [1.229, 1.493, 1.232],
    [1.847, 1.810, 1.699],
    [1.847, 1.810, 1.699],
    [1.251, 1.087, 1.376],
    [1.136, 1.133, 1.286],
    [1.136, 1.133, 1.286],
    [1.363, 1.219, 1.390],
    [1.325, 1.303, 1.279]
])



hand_results = np.array([
    [2.178, 1.778, 2.411],
    [1.611, 1.604, 2.180],
    [1.250, 1.296, 1.001],
    [1.251, 1.098, 1.408],
    [0.671, 0.690, 0.670],
    [0.691, 0.691, 0.676],
    [0.697, 0.694, 0.713],
    [0.733, 0.722, 0.716]
])

pelvis_results = np.array([
    [2.216, 2.281, 2.312],
    [2.633, 2.291, 2.410],
    [2.184, 2.321, 2.296],
    [2.408, 2.268, 2.199],
    [2.294, 2.305, 2.271],
    [2.294, 2.354, 2.238],
    [2.426, 2.420, 2.339],
    [2.385, 2.413, 2.413]
])

ultra_results = np.array([
    [7.776, 7.193, 7.343],
    [7.914, 6.798, 7.113],
    [7.493, 6.856, 7.170],
    [7.080, 7.568, 7.256],
    [6.904, 7.032, 8.962],
    [6.689, 7.031, 6.595],
    [6.986, 7.685, 6.867],
    [7.252, 7.188, 7.131]
])

def print_state(results):
    print("start")
    means = np.mean(results, axis=1)
    stds = np.std(results, axis=1)
    for mean, std in zip(means, stds):
        msg = "{:.3f}$\pm${:.3f}".format(mean, std)
        print(msg)

for arr in [ceph_results, hand_results, pelvis_results, ultra_results]:
    print_state(arr)