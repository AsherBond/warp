/** Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
 * NVIDIA CORPORATION and its licensors retain all intellectual property
 * and proprietary rights in and to this software, related documentation
 * and any modifications thereto.  Any use, reproduction, disclosure or
 * distribution of this software and related documentation without an express
 * license agreement from NVIDIA CORPORATION is strictly prohibited.
 */

#pragma once

#include <stddef.h>

void radix_sort_reserve(void* context, int n, void** mem_out=NULL, size_t* size_out=NULL);
void radix_sort_pairs_host(int* keys, int* values, int n);
void radix_sort_pairs_host(float* keys, int* values, int n);
void radix_sort_pairs_host(int64_t* keys, int* values, int n);
void radix_sort_pairs_device(void* context, int* keys, int* values, int n);
void radix_sort_pairs_device(void* context, float* keys, int* values, int n);
void radix_sort_pairs_device(void* context, int64_t* keys, int* values, int n);

void segmented_sort_pairs_host(float* keys, int* values, int n, int* segment_start_indices, int* segment_end_indices, int num_segments);
void segmented_sort_pairs_device(void* context, float* keys, int* values, int n, int* segment_start_indices, int* segment_end_indices, int num_segments);
void segmented_sort_pairs_host(void* context, int* keys, int* values, int n, int* segment_start_indices, int* segment_end_indices, int num_segments);
void segmented_sort_pairs_device(void* context, int* keys, int* values, int n, int* segment_start_indices, int* segment_end_indices, int num_segments);
