#include "face_utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// read_data_from_file 已在 utils/file_utils.c 中定义，此处不再重复

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
