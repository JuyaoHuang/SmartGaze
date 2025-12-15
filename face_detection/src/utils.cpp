#include "face_utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/**
 * @brief 从文件读取数据
 */
int read_data_from_file(const char *filename, char **data) {
    if (!filename || !data) {
        return -1;
    }

    FILE *fp = fopen(filename, "rb");
    if (!fp) {
        printf("[utils] Error: Cannot open file %s\n", filename);
        return -1;
    }

    // 获取文件大小
    fseek(fp, 0, SEEK_END);
    int size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    if (size <= 0) {
        fclose(fp);
        return -1;
    }

    // 分配内存
    *data = (char *)malloc(size);
    if (!*data) {
        fclose(fp);
        return -1;
    }

    // 读取数据
    size_t read_size = fread(*data, 1, size, fp);
    fclose(fp);

    if (read_size != (size_t)size) {
        free(*data);
        *data = NULL;
        return -1;
    }

    return size;
}

/**
 * @brief 计算余弦相似度
 */
float cosine_similarity(const float *embedding1, const float *embedding2, int dim) {
    if (!embedding1 || !embedding2 || dim <= 0) {
        return 0.0f;
    }

    float dot_product = 0.0f;
    float norm1 = 0.0f;
    float norm2 = 0.0f;

    for (int i = 0; i < dim; i++) {
        dot_product += embedding1[i] * embedding2[i];
        norm1 += embedding1[i] * embedding1[i];
        norm2 += embedding2[i] * embedding2[i];
    }

    norm1 = sqrtf(norm1);
    norm2 = sqrtf(norm2);

    if (norm1 < 1e-6f || norm2 < 1e-6f) {
        return 0.0f;
    }

    return dot_product / (norm1 * norm2);
}
