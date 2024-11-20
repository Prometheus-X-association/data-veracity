plugins {
    id("buildlogic.java-application-conventions")
}

dependencies {
    implementation(project(":utilities"))
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva"
}
