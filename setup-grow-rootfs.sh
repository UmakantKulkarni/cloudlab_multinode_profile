#!/usr/bin/env bash

# Detect the root partition using the `findmnt` command
ROOT_PART=$(findmnt -n -o SOURCE /)

# Extract the disk device from the root partition (e.g., /dev/sda3 -> /dev/sda)
DISK=$(lsblk -no pkname "$ROOT_PART")
DISK_PATH="/dev/$DISK"

# Extract the partition number from the root partition (e.g., /dev/sda3 -> 3)
PART_NUM=$(echo "$ROOT_PART" | grep -o '[0-9]*$')

echo "Detected root partition: $ROOT_PART"
echo "Detected disk: $DISK_PATH"
echo "Detected partition number: $PART_NUM"

# Start the partition resizing using fdisk in a non-interactive manner
(
echo d     # Delete the root partition
echo "$PART_NUM"  # Partition number to delete
echo n     # Create a new partition
echo "$PART_NUM"  # Use the same partition number
echo       # Default first sector
echo       # Default last sector to use all available space
echo p     # Print the partition table to verify
echo w     # Write the changes
) | fdisk "$DISK_PATH"

# Inform the kernel about the partition table change
partprobe "$DISK_PATH"

# Resize the file system on the root partition
echo "Resizing the filesystem on $ROOT_PART"
resize2fs "$ROOT_PART"

# Display the updated disk usage
echo "Filesystem after resizing:"
df -hT

echo "Root partition resize complete."
