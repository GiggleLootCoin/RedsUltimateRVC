#include "rvc.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: pth-check MODEL.pth\n");
        return 2;
    }
    rvc_model_t *model = (rvc_model_t *)calloc(1, sizeof(*model));
    if (!model) return 3;
    if (rvc_load(model, argv[1]) != 0) {
        fprintf(stderr, "PTH loader rejected the checkpoint.\n");
        free(model);
        return 4;
    }
    printf("PTH_OK ques=%d sample_rate=%d fps=%d version=%d speakers=%d\n",
           model->cfg.ques, model->cfg.sr, model->fps,
           model->cfg.version, model->emb_g_dim > 0 ? 1 : 0);
    const int supported = model->cfg.ques == 768 &&
        (model->cfg.sr == 32000 || model->cfg.sr == 40000 || model->cfg.sr == 48000) &&
        model->fps > 0;
    rvc_free(model);
    free(model);
    return supported ? 0 : 5;
}
