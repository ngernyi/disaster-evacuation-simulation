from mapConverter import *
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from skimage.morphology import erosion, square
import numpy as np
from skimage.morphology import skeletonize
from scipy.ndimage import convolve

# def shrink_to_one_tile(free_map):
#     # free_map: 1 = free, 0 = wall
#     result = free_map.copy()
#     while np.sum(result) > 1:  # stop when only 1 free remains
#         eroded = erosion(result, square(3))
#         if np.sum(eroded) == 0:  # if erosion kills everything, keep last result
#             break
#         result = eroded
        
#     #  calculate the number of free neighbours
#     free_neighbours = erosion(1 - result, square(3))
#     print("free_neighbours", np.sum(free_neighbours))
#     return result

# def thin_to_one_tile(filled_map):
#     """
#     filled_map: 2D numpy array
#                 1 = wall
#                 0 = free
#     Returns: skeletonized map with walkable paths reduced to 1-tile wide
#     """
#     # In skeletonize, 1 = foreground (path), 0 = background (wall)
#     inverted = 1 - filled_map   # now free=1, wall=0
    
#     # Skeletonize free space
#     skeleton = skeletonize(inverted).astype(np.uint8)
    
#     # Return skeleton as free=1, wall=0
#     result = skeleton
#     return result

    
    # 
    


# get the filled map and minMaxXY
filled_map, minMaxXY = read_filled_grid_and_minMaxXY(
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\filled_grid.npy", 
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\minMaxXY.npy"
    )

def skeletonize_map(free_map):
    # Convert to boolean (skeletonize needs True/False)
    skeleton = skeletonize(free_map.astype(bool))
    return skeleton.astype(np.uint8)



def skeletonize_map(free_map):
    skeleton = skeletonize(free_map.astype(bool))
    return skeleton.astype(np.uint8)

def find_nodes(skeleton):
    # Define 8-neighborhood kernel
    kernel = np.array([[1,1,1],
                       [1,0,1],
                       [1,1,1]])
    
    # Count neighbors for each pixel
    neighbor_count = convolve(skeleton, kernel, mode='constant')
    
    # Identify nodes
    junctions = ((skeleton == 1) & (neighbor_count >= 3))  # intersections
    dead_ends = ((skeleton == 1) & (neighbor_count == 1))  # endpoints
    
    return junctions, dead_ends, neighbor_count


skeleton = skeletonize_map(filled_map)
junctions, dead_ends, neighbor_count = find_nodes(skeleton)

np.save("skeleton.npy", skeleton)
np.save("junctions.npy", junctions)
np.save("dead_ends.npy", dead_ends)
np.save("neighbor_count.npy", neighbor_count)


# plt.imshow(skeleton, cmap='gray')
# plt.scatter(*np.where(junctions)[::-1], c='red', label='Junctions')
# plt.scatter(*np.where(dead_ends)[::-1], c='blue', label='Dead-ends')
# plt.legend()
# plt.show()

