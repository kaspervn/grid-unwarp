
__kernel void map_coordinates_nn(__global __read_only uchar* input,
                  __global __read_only float* x_map,
                  __global __read_only float* y_map,
                  __global __write_only uchar* output,
                  ulong input_stride)
{
    int out_idx = get_global_id(1) + get_global_id(0)*get_global_size(1);

    int src_x = x_map[out_idx];
    int src_y = y_map[out_idx];
    src_x = clamp(src_x, 0, 1280);
    src_y = clamp(src_y, 0, 960);

    //nearest neighbor
    output[out_idx] = input[src_x + input_stride*src_y];
}

__kernel void map_coordinates(__global __read_only uchar* input,
                  __global __read_only float* x_map,
                  __global __read_only float* y_map,
                  __global __write_only uchar* output,
                  ulong input_stride)
{
    int out_idx = get_global_id(1) + get_global_id(0)*get_global_size(1);

    float x = x_map[out_idx];
    float y = y_map[out_idx];
    float x1 = floor(x);
    float y1 = floor(y);
    float x2 = x1 + 1.0f;
    float y2 = y1 + 1.0f;

    float ax = (x2 - x) / (x2 - x1);
    float bx = (x - x1) / (x2 - x1);
    float q11 = input[(int)x + input_stride*((int)y)];
    float q12 = input[(int)x + input_stride*((int)y + 1)];
    float q21 = input[(int)x + 1 + input_stride*((int)y)];
    float q22 = input[(int)x + 1 + input_stride*((int)y + 1)];

    float val = (y2 - y) / (y2 - y1) * (ax * q11 + bx * q21) + (y - y1) / (y2 - y1) * (ax * q12 + bx * q22);

    output[out_idx] = (uchar)val;
}