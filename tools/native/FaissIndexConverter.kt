package com.ultimatervc.mobile

import android.app.ActivityManager
import android.content.Context
import com.developermindset.faiss.FAISS
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Converts standard RVC v2 FAISS indexes into the app's local mobile.index
 * format. Everything runs on-device; the source index is never uploaded.
 */
object FaissIndexConverter {
    private const val FEATURE_DIMENSION = 768
    private const val MAX_SOURCE_BYTES = 512L * 1024L * 1024L
    private const val MAX_OUTPUT_BYTES = 1_500_000_000L
    private val MAGIC = "URVCIDX1".toByteArray(Charsets.US_ASCII)

    fun convert(context: Context, source: File): ManagedImportedFile {
        require(source.isFile && source.length() > 16L) {
            "Choose a non-empty standard RVC .index file."
        }
        require(source.name.lowercase().endsWith(".index") && !source.name.lowercase().endsWith(".mobile.index")) {
            "Choose a standard FAISS .index file, not an existing .mobile.index."
        }
        require(source.length() <= MAX_SOURCE_BYTES) {
            "This index is larger than the 512 MB on-phone conversion limit."
        }

        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memory = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memory)
        val minimumAvailable = source.length() * 3L / 2L + 192L * 1024L * 1024L
        require(memory.availMem >= minimumAvailable) {
            "There is not enough free memory to safely convert this index. Close other apps and try again."
        }

        val index = try {
            FAISS.readIndex(source.absolutePath)
        } catch (error: Throwable) {
            throw IllegalArgumentException("This file is not a readable FAISS index: ${error.message ?: "invalid index"}", error)
        }

        val temporaryDirectory = File(context.cacheDir, "faiss_index_convert").apply { mkdirs() }
        val baseName = source.name.removeSuffix(".index")
            .replace(Regex("[^A-Za-z0-9._()-]"), "_")
            .take(120)
            .ifBlank { "rvc_voice" }
        val temporary = File(temporaryDirectory, "$baseName.mobile.index.partial")
        val completed = File(temporaryDirectory, "$baseName.mobile.index")

        try {
            require(index.isTrained()) { "The FAISS index has not been trained." }
            require(index.dimension() == FEATURE_DIMENSION) {
                "This index is ${index.dimension()}-dimensional. The mobile converter currently supports 768-dimensional RVC v2 indexes."
            }
            val total = index.ntotal()
            require(total > 0L) { "The FAISS index contains no feature vectors." }
            val expectedBytes = 12L + total * FEATURE_DIMENSION.toLong() * Float.SIZE_BYTES.toLong()
            require(expectedBytes <= MAX_OUTPUT_BYTES) {
                "The converted index would be larger than 1.5 GB, which is too large for this phone."
            }
            require(context.cacheDir.usableSpace >= expectedBytes + 32L * 1024L * 1024L) {
                "There is not enough temporary storage to convert this index."
            }
            require(context.filesDir.usableSpace >= expectedBytes + 32L * 1024L * 1024L) {
                "There is not enough internal storage for the converted mobile index."
            }

            temporary.delete()
            completed.delete()
            val exported = index.exportMobileIndex(temporary.absolutePath)
            require(exported == total) {
                "FAISS exported $exported vectors, but the source index contains $total."
            }
            validateMobileIndex(temporary, total)
            if (!temporary.renameTo(completed)) {
                temporary.copyTo(completed, overwrite = true)
                temporary.delete()
                validateMobileIndex(completed, total)
            }

            return TempWorkspaceManager(context.filesDir, context.cacheDir)
                .importPickedFile(ImportedFileKind.INDEX, completed.absolutePath)
        } catch (error: Throwable) {
            throw IllegalStateException(error.message ?: "FAISS index conversion failed.", error)
        } finally {
            index.close()
            temporary.delete()
            completed.delete()
        }
    }

    private fun validateMobileIndex(file: File, expectedVectors: Long) {
        require(file.isFile && file.length() >= 12L) {
            "The converted mobile index is missing or incomplete."
        }
        RandomAccessFile(file, "r").use { input ->
            val magic = ByteArray(8)
            input.readFully(magic)
            require(magic.contentEquals(MAGIC)) {
                "The converted file does not have the mobile index signature."
            }
            val countBytes = ByteArray(4)
            input.readFully(countBytes)
            val count = ByteBuffer.wrap(countBytes).order(ByteOrder.LITTLE_ENDIAN).int
            require(count > 0 && count.toLong() == expectedVectors) {
                "The converted mobile index has an invalid vector count."
            }
            val expectedLength = 12L + count.toLong() * FEATURE_DIMENSION * Float.SIZE_BYTES
            require(file.length() == expectedLength) {
                "The converted mobile index has an invalid file length."
            }
        }
    }
}
