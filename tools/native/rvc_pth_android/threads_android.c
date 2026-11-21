#include "threads.h"
#include <pthread.h>
#include <stdlib.h>

#ifndef RED_RVC_MAX_THREADS
#define RED_RVC_MAX_THREADS 4
#endif

typedef struct {
    int begin;
    int end;
    spcv_par_fn fn;
    void *ctx;
} red_rvc_job;

static void *red_rvc_worker(void *opaque) {
    red_rvc_job *job = (red_rvc_job *)opaque;
    job->fn(job->begin, job->end, job->ctx);
    return NULL;
}

int spcv_nthreads(void) {
    return RED_RVC_MAX_THREADS;
}

void spcv_par_for(int n, spcv_par_fn fn, void *ctx) {
    if (n <= 0 || fn == NULL) return;

    int workers = RED_RVC_MAX_THREADS;
    int useful = n / 1024;
    if (useful < 1) useful = 1;
    if (workers > useful) workers = useful;
    if (workers > n) workers = n;
    if (workers <= 1) {
        fn(0, n, ctx);
        return;
    }

    pthread_t threads[RED_RVC_MAX_THREADS];
    red_rvc_job jobs[RED_RVC_MAX_THREADS];
    int started[RED_RVC_MAX_THREADS] = {0};
    int base = n / workers;
    int remainder = n % workers;
    int begin = 0;

    for (int i = 0; i < workers; ++i) {
        int count = base + (i < remainder ? 1 : 0);
        jobs[i].begin = begin;
        jobs[i].end = begin + count;
        jobs[i].fn = fn;
        jobs[i].ctx = ctx;
        begin += count;

        if (pthread_create(&threads[i], NULL, red_rvc_worker, &jobs[i]) == 0) {
            started[i] = 1;
        } else {
            fn(jobs[i].begin, jobs[i].end, ctx);
        }
    }

    for (int i = 0; i < workers; ++i) {
        if (started[i]) pthread_join(threads[i], NULL);
    }
}
