plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.7.0"
}

rootProject.name = "dva"
include(
    "api",
    "app",
    "model",
    "utilities",
)
