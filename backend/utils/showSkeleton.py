import numpy as np
import matplotlib.pyplot as plt

# Load the 2D array from the .npy file
skeleton = np.load("filled_grid.npy")

# Optional: check its shape and unique values
print("Array shape:", skeleton.shape)
print("Unique values:", np.unique(skeleton))

# Plot the array
plt.figure(figsize=(8, 8))
# Use cmap='gray' so 1s are white and 0s are black (origin='lower' flips y-axis if desired)
plt.imshow(skeleton, cmap='gray', origin='lower')

plt.title("Wall Plot")
plt.axis('off')  # Hide axes for cleaner view
plt.savefig("wall_lv1.png")
