using UnrealBuildTool;
using System.Collections.Generic;

public class SoulwoodGameTarget : TargetRules
{
    public SoulwoodGameTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        ExtraModuleNames.Add("soulwoodgame");
    }
}
