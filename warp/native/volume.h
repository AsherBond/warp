/** Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
 * NVIDIA CORPORATION and its licensors retain all intellectual property
 * and proprietary rights in and to this software, related documentation
 * and any modifications thereto.  Any use, reproduction, disclosure or
 * distribution of this software and related documentation without an express
 * license agreement from NVIDIA CORPORATION is strictly prohibited.
 */

#pragma once

#include "builtin.h"

#define PNANOVDB_C
#ifdef WP_CUDA
#    define PNANOVDB_MEMCPY_CUSTOM
#    define pnanovdb_memcpy memcpy
#endif
#include "nanovdb/PNanoVDB.h"

namespace wp
{
struct Volume
{
    static constexpr int CLOSEST = 0;
    static constexpr int LINEAR = 1;

    pnanovdb_buf_t buf;
    pnanovdb_grid_handle_t grid;
    pnanovdb_tree_handle_t tree;

    uint64_t size_in_bytes;
};

// Sampling the volume at the given index-space coordinates, uvw can be fractional
CUDA_CALLABLE inline float volume_sample_local(uint64_t id, vec3 uvw, int sampling_mode)
{
    const Volume volume = *(const Volume*)(id);
    const pnanovdb_root_handle_t root = pnanovdb_tree_get_root(volume.buf, volume.tree);
    const pnanovdb_vec3_t uvw_pnano{ uvw.x, uvw.y, uvw.z };

    if (sampling_mode == Volume::CLOSEST)
    {
        const pnanovdb_coord_t ijk = pnanovdb_vec3_round_to_coord(uvw_pnano);
        const pnanovdb_address_t address =
            pnanovdb_root_get_value_address(PNANOVDB_GRID_TYPE_FLOAT, volume.buf, root, PNANOVDB_REF(ijk));
        return pnanovdb_read_float(volume.buf, address);
    }
    else if (sampling_mode == Volume::LINEAR)
    {
        constexpr pnanovdb_coord_t OFFSETS[] = {
            { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 0, 1, 1 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 0 }, { 1, 1, 1 },
        };

        const pnanovdb_vec3_t ijk_base{ floorf(uvw_pnano.x), floorf(uvw_pnano.y), floorf(uvw_pnano.z) };
        const pnanovdb_vec3_t ijk_frac{ uvw_pnano.x - ijk_base.x, uvw_pnano.y - ijk_base.y, uvw_pnano.z - ijk_base.z };
        const pnanovdb_coord_t ijk{ (pnanovdb_int32_t)ijk_base.x, (pnanovdb_int32_t)ijk_base.y, (pnanovdb_int32_t)ijk_base.z };

        pnanovdb_readaccessor_t accessor;
        pnanovdb_readaccessor_init(PNANOVDB_REF(accessor), root);
        float val = 0.0f;
        const float wx[2]{ 1 - ijk_frac.x, ijk_frac.x };
        const float wy[2]{ 1 - ijk_frac.y, ijk_frac.y };
        const float wz[2]{ 1 - ijk_frac.z, ijk_frac.z };
#pragma unroll
        for (int idx = 0; idx < 8; ++idx)
        {
            const pnanovdb_coord_t& offs = OFFSETS[idx];
            const pnanovdb_coord_t ijkShifted = pnanovdb_coord_add(ijk, offs);
            pnanovdb_address_t address = pnanovdb_readaccessor_get_value_address(
                PNANOVDB_GRID_TYPE_FLOAT, volume.buf, PNANOVDB_REF(accessor), PNANOVDB_REF(ijkShifted));
            val += wx[offs.x] * wy[offs.y] * wz[offs.z] * pnanovdb_read_float(volume.buf, address);
        }
        return val;
    }
    return 0;
}

CUDA_CALLABLE inline void adj_volume_sample_local(
    uint64_t id, vec3 uvw, int sampling_mode, uint64_t& adj_id, vec3& adj_uvW, int& adj_sampling_mode, float& adj_result)
{
}

// Sampling the volume at the given world-space coordinates
CUDA_CALLABLE inline float volume_sample_world(uint64_t id, vec3 xyz, int sampling_mode)
{
    const Volume volume = *(const Volume*)(id);
    const pnanovdb_root_handle_t root = pnanovdb_tree_get_root(volume.buf, volume.tree);

    const pnanovdb_vec3_t xyz_pnano{ xyz.x, xyz.y, xyz.z };
    const pnanovdb_vec3_t uvw_pnano = pnanovdb_grid_world_to_indexf(volume.buf, volume.grid, PNANOVDB_REF(xyz_pnano));
    const vec3 uvw{ uvw_pnano.x, uvw_pnano.y, uvw_pnano.z };

    return volume_sample_local(id, uvw, sampling_mode);
}

CUDA_CALLABLE inline void adj_volume_sample_world(
    uint64_t id, vec3 xyz, int sampling_mode, uint64_t& adj_id, vec3& adj_xyz, int& adj_sampling_mode, float& adj_result)
{
}

CUDA_CALLABLE inline float volume_lookup(uint64_t id, int32_t i, int32_t j, int32_t k)
{
    const Volume volume = *(const Volume*)(id);
    const pnanovdb_root_handle_t root = pnanovdb_tree_get_root(volume.buf, volume.tree);

    const pnanovdb_coord_t ijk{ i, j, k };
    const pnanovdb_address_t address =
        pnanovdb_root_get_value_address(PNANOVDB_GRID_TYPE_FLOAT, volume.buf, root, PNANOVDB_REF(ijk));
    return pnanovdb_read_float(volume.buf, address);
}

CUDA_CALLABLE inline void adj_volume_lookup(
    uint64_t id, int32_t i, int32_t j, int32_t k, uint64_t& adj_id, int32_t& adj_i, int32_t& adj_j, int32_t& adj_k, float& adj_result)
{
}

// Index- to world-space space transformation
CUDA_CALLABLE inline vec3 volume_transform(uint64_t id, vec3 uvw)
{
    const Volume volume = *(const Volume*)(id);
    const pnanovdb_vec3_t pos{ uvw.x, uvw.y, uvw.z };
    const pnanovdb_vec3_t xyz = pnanovdb_grid_index_to_worldf(volume.buf, volume.grid, PNANOVDB_REF(pos));
    return { xyz.x, xyz.y, xyz.z };
}

CUDA_CALLABLE inline void adj_volume_transform(uint64_t id, vec3 uvw, uint64_t& adj_id, vec3& adj_uvw, vec3& result)
{
}

// World- to index-space transformation
CUDA_CALLABLE inline vec3 volume_transform_inv(uint64_t id, vec3 xyz)
{
    const Volume volume = *(const Volume*)(id);
    const pnanovdb_vec3_t pos{ xyz.x, xyz.y, xyz.z };
    const pnanovdb_vec3_t uvw = pnanovdb_grid_world_to_indexf(volume.buf, volume.grid, PNANOVDB_REF(pos));
    return { uvw.x, uvw.y, uvw.z };
}

CUDA_CALLABLE inline void adj_volume_transform_inv(uint64_t id, vec3 xyz, uint64_t& adj_id, vec3& adj_xyz, vec3& result)
{
}


} // namespace wp
