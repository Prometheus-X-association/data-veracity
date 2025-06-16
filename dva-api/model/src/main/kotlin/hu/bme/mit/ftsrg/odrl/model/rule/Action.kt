package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.serialization.odrl.ActionSerializer
import kotlinx.serialization.Serializable

@Serializable(with = ActionSerializer::class)
enum class Action(val w3cInstance: String) {
  ATTRIBUTION("Attribution"),
  COMMERCIAL_USE("Commercial Use"),
  DERIVATIVE_WORKS("Derivative Works"),
  DISTRIBUTION("Distribution"),
  NOTICE("Notice"),
  REPRODUCTION("Reproduction"),
  SHARE_ALIKE("ShareAlike"),
  SHARING("Sharing"),
  SOURCE_CODE("SourceCode"),
  ACCEPT_TRACKING("acceptTracking"),
  AD_HOC_SHARE("adHocShare"),
  AGGREGATE("aggregate"),
  ANNOTATE("annotate"),
  ANONYMIZE("anonymize"),
  ARCHIVE("archive"),
  ATTRIBUTE("attribute"),
  COMPENSATE("compensate"),
  CONCURRENT_USE("concurrentUse"),
  COPY("copy"),
  DELETE("delete"),
  DERIVE("derive"),
  DIGITIZE("digitize"),
  DISPLAY("display"),
  DISTRIBUTE("distribute"),
  ENSURE_EXCLUSIVITY("ensureExclusivity"),
  EXECUTE("execute"),
  EXPORT("export"),
  EXTRACT("extract"),
  EXTRACT_CHAR("extractChar"),
  EXTRACT_PAGE("extractPage"),
  EXTRACT_WORD("extractWord"),
  GIVE("give"),
  GRANT_USE("grantUse"),
  INCLUDE("include"),
  INDEX("index"),
  INFORM("inform"),
  INSTALL("install"),
  MODIFY("modify"),
  MOVE("move"),
  NEXT_POLICY("nextPolicy"),
  OBTAIN_CONSENT("obtainConsent"),
  PLAY("play"),
  PRESENT("present"),
  PREVIEW("preview"),
  PRINT("print"),
  READ("read"),
  REPRODUCE("reproduce"),
  REVIEW_POLICY("reviewPolicy"),
  SECONDARY_USE("secondaryUse"),
  SELL("sell"),
  SHARE("share"),
  STREAM("stream"),
  SYNCHRONIZE("synchronize"),
  TEXT_TO_SPEECH("textToSpeech"),
  TRANSFER("transfer"),
  TRANSFORM("transform"),
  TRANSLATE("translate"),
  UNINSTALL("uninstall"),
  USE("use"),
  WATERMARK("watermark"),

  @Deprecated(
    "The shareAlike identifier has been deprecated by the standard for the Creative Commons ShareAlike identifier",
    ReplaceWith("Action.SHARE_ALIKE")
  )
  CC_SHARE_ALIKE("shareAlike"),

  @Deprecated(
    "The attachPolicy identifier has been deprecated by the standard for the Creative Commons Notice identifier",
    ReplaceWith("Action.NOTICE")
  )
  CC_ATTACH_POLICY("attachPolicy"),

  @Deprecated(
    "The commercialize identifier has been deprecated by the standard for the Creative Commons CommercialUse identifier",
    ReplaceWith("Action.COMMERCIAL_USE")
  )
  CC_COMMERCIALIZE("commercialize"),

  @Deprecated(
    "The attachSource identifier has been deprecated by the standard for the Creative Commons SourceCode identifier",
    ReplaceWith("Action.SOURCE_CODE")
  )
  CC_ATTACH_SOURCE("attachSource"),

  @Deprecated(
    "The write and writeTo identifiers have been deprecated by the standard for the modify identifier",
    ReplaceWith("Action.MODIFY")
  )
  WRITE("write"),

  @Deprecated(
    "The write and writeTo identifiers have been deprecated by the standard for the modify identifier",
    ReplaceWith("Action.MODIFY")
  )
  WRITE_TO("writeTo"),

  @Deprecated(
    "The append and appendTo identifiers have been deprecated by the standard for the modify identifier",
    ReplaceWith("Action.MODIFY")
  )
  APPEND("append"),

  @Deprecated(
    "The append and appendTo identifiers have been deprecated by the standard for the modify identifier",
    ReplaceWith("Action.MODIFY")
  )
  APPEND_TO("appendTo"),

  @Deprecated(
    "The pay identifier has been deprecated by the standard for the compensate identifier",
    ReplaceWith("Action.COMPENSATE")
  )
  PAY("pay"),

  @Deprecated(
    "The lend identifier has been deprecated by the standard without replacement",
  )
  LEND("lend"),

  @Deprecated(
    "The lease identifier has been deprecated by the standard without replacement",
  )
  LEASE("lease"),

  @Deprecated(
    "The license identifier has been deprecated by the standard for the grantUse identifier",
    ReplaceWith("Action.GRANT_USE")
  )
  LICENSE("license"),
}