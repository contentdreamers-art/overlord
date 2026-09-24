#include "SoulwoodGameplay.h"
#include "Camera/CameraComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/DamageType.h"
#include "Materials/MaterialInterface.h"
#include "Math/RotationMatrix.h"
#include "Animation/AnimSequence.h"
#include "UObject/ConstructorHelpers.h"

namespace Soulwood
{
    template<typename T> T* Asset(const TCHAR* Path)
    {
        return LoadObject<T>(nullptr, Path);
    }
    constexpr float NormalSpeed = 480.f;
    constexpr float FastSpeed = 2400.f;
}

ASoulwoodProjectile::ASoulwoodProjectile()
{
    PrimaryActorTick.bCanEverTick = false;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    SetRootComponent(Collision);
    Collision->InitSphereRadius(18.f);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Collision->SetCollisionObjectType(ECC_WorldDynamic);
    Collision->SetCollisionResponseToAllChannels(ECR_Overlap);
    Collision->OnComponentBeginOverlap.AddDynamic(this, &ASoulwoodProjectile::OnOverlap);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisibleProjectile"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("ProjectileGlow"));
    Glow->SetupAttachment(Collision);
    Glow->SetIntensity(2500.f);
    Glow->SetAttenuationRadius(400.f);
    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    Movement->InitialSpeed = 3600.f;
    Movement->MaxSpeed = 3600.f;
    Movement->ProjectileGravityScale = 0.f;
    InitialLifeSpan = 8.f;
}

void ASoulwoodProjectile::Configure(bool bIsFireball, const FVector& Velocity, float Damage)
{
    bFireball = bIsFireball;
    HitDamage = Damage;
    const float Speed = bFireball ? 2800.f : 5200.f;
    Movement->InitialSpeed = Speed;
    Movement->MaxSpeed = Speed;
    Movement->Velocity = Velocity.GetSafeNormal() * Speed;
    Movement->ProjectileGravityScale = bFireball ? 0.f : .17f;
    if (bFireball)
    {
        Visual->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere")));
        Visual->SetRelativeScale3D(FVector(.5f));
        Visual->SetMaterial(0, Soulwood::Asset<UMaterialInterface>(TEXT("/Game/SoulwoodOriginal/Materials/M_FireSoul.M_FireSoul")));
        Glow->SetLightColor(FLinearColor(1.f, .12f, .015f));
        Collision->SetSphereRadius(35.f);
    }
    else
    {
        Visual->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Game/SoulwoodOriginal/Meshes/SM_Arrow.SM_Arrow")));
        Visual->SetRelativeRotation(FRotator(0, 90, 0));
        Glow->SetIntensity(0.f);
        Collision->SetSphereRadius(12.f);
    }
}

void ASoulwoodProjectile::OnOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*,
    int32, bool, const FHitResult&)
{
    if (!Other || Other == this || Other == GetOwner() || Other->IsA(ASoulwoodProjectile::StaticClass()))
        return;
    if (Other->IsA(ASoulwoodGoblin::StaticClass()) || Other->IsA(ASoulwoodHero::StaticClass()))
        UGameplayStatics::ApplyDamage(Other, HitDamage, GetInstigatorController(), this, UDamageType::StaticClass());
    if (Other->IsA(ASoulwoodReward::StaticClass()))
        return;
    Destroy();
}

ASoulwoodReward::ASoulwoodReward()
{
    PrimaryActorTick.bCanEverTick = true;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("PickupSphere"));
    SetRootComponent(Collision);
    Collision->InitSphereRadius(45.f);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SoulOrb"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere")));
    Visual->SetRelativeScale3D(FVector(.45f));
    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("SoulGlow"));
    Glow->SetupAttachment(Collision);
    Glow->SetIntensity(1600.f);
    Glow->SetAttenuationRadius(580.f);
    InitialLifeSpan = 60.f;
}

void ASoulwoodReward::Initialize(ESoulwoodReward InType, ASoulwoodHero* InOwner)
{
    RewardType = InType;
    Recipient = InOwner;
    StartLocation = GetActorLocation();
    const TCHAR* Path = TEXT("/Game/SoulwoodOriginal/Materials/M_FireSoul.M_FireSoul");
    FLinearColor LightColor(1.f, .55f, .04f);
    if (InType == ESoulwoodReward::Beast)
    {
        Path = TEXT("/Game/SoulwoodOriginal/Materials/M_BeastSoul.M_BeastSoul");
        LightColor = FLinearColor(.02f, .43f, 1.f);
    }
    else if (InType == ESoulwoodReward::Angel)
    {
        Path = TEXT("/Game/SoulwoodOriginal/Materials/M_AngelSoul.M_AngelSoul");
        LightColor = FLinearColor(1.f, .94f, .74f);
    }
    Visual->SetMaterial(0, Soulwood::Asset<UMaterialInterface>(Path));
    Glow->SetLightColor(LightColor);
}

void ASoulwoodReward::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    TimeAlive += DeltaTime;
    if (!IsValid(Recipient)) return;
    const FVector Dest = Recipient->GetActorLocation() + FVector(0, 0, 90);
    const float Distance = FVector::Dist(GetActorLocation(), Dest);
    if (Distance < 1000.f)
    {
        FVector Tangent = FVector::CrossProduct((Dest - GetActorLocation()).GetSafeNormal(), FVector::UpVector);
        const float Curve = FMath::Sin(TimeAlive * 7.f) * FMath::Min(Distance * .12f, 85.f);
        SetActorLocation(FMath::VInterpTo(GetActorLocation(), Dest + Tangent * Curve,
            DeltaTime, 1.5f + 720.f / FMath::Max(Distance, 90.f)));
        if (Distance < 85.f)
        {
            Recipient->Absorb(RewardType);
            Destroy();
        }
    }
    else
    {
        SetActorLocation(StartLocation + FVector(0,0, FMath::Sin(TimeAlive*2.4f)*22.f));
        Visual->SetRelativeScale3D(FVector(.44f + .035f*FMath::Sin(TimeAlive*4.f)));
    }
}

ASoulwoodGoblin::ASoulwoodGoblin()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(44.f, 92.f);
    GetCharacterMovement()->MaxWalkSpeed = 235.f;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetMesh()->SetRelativeLocation(FVector(0,0,-90));
    GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
    Sword = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RustySword"));
    Sword->SetupAttachment(GetMesh(), TEXT("lower_arm_R"));
    Sword->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void ASoulwoodGoblin::BeginPlay()
{
    Super::BeginPlay();
    GetMesh()->SetSkeletalMeshAsset(Soulwood::Asset<USkeletalMesh>(TEXT("/Game/SoulwoodOriginal/Characters/SK_Goblin.SK_Goblin")));
    Sword->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Game/SoulwoodOriginal/Meshes/SM_Arrow.SM_Arrow")));
    IdleAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_GoblinSK_Goblin_Goblin_Idle.SK_GoblinSK_Goblin_Goblin_Idle"));
    WalkAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_GoblinSK_Goblin_Goblin_Walk.SK_GoblinSK_Goblin_Goblin_Walk"));
    AttackAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_GoblinSK_Goblin_Goblin_Attack.SK_GoblinSK_Goblin_Goblin_Attack"));
    DeathAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_GoblinSK_Goblin_Goblin_Death.SK_GoblinSK_Goblin_Goblin_Death"));
    GetCharacterMovement()->bRunPhysicsWithNoController = true;
    PlayState(IdleAnimation, true);
    Target = Cast<ASoulwoodHero>(UGameplayStatics::GetPlayerCharacter(this, 0));
}

void ASoulwoodGoblin::PlayState(UAnimSequence* Animation, bool bLoop)
{
    if (Animation && CurrentAnimation != Animation)
    {
        GetMesh()->PlayAnimation(Animation, bLoop);
        CurrentAnimation = Animation;
    }
}

void ASoulwoodGoblin::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (!IsValid(Target)) Target = Cast<ASoulwoodHero>(UGameplayStatics::GetPlayerCharacter(this, 0));
    if (bDead || !IsValid(Target)) return;
    const FVector ToPlayer = Target->GetActorLocation() - GetActorLocation();
    const float Distance = ToPlayer.Size2D();
    AttackCooldown = FMath::Max(0.f, AttackCooldown - DeltaTime);
    if (bWindingUp)
    {
        PlayState(AttackAnimation, false);
        AttackClock += DeltaTime;
        if (AttackClock >= .62f)
        {
            bWindingUp = false;
            AttackClock = 0.f;
            if (Distance < 215.f)
                UGameplayStatics::ApplyDamage(Target, 16.f, GetController(), this, UDamageType::StaticClass());
            AttackCooldown = 1.5f;
        }
    }
    else if (Distance < 175.f && AttackCooldown <= 0.f)
    {
        bWindingUp = true;
        AttackClock = 0.f;
    }
    else if (Distance < 1800.f && Distance > 150.f)
    {
        PlayState(WalkAnimation, true);
        AddMovementInput(ToPlayer.GetSafeNormal2D(), 1.f);
    }
    else PlayState(IdleAnimation, true);
    if (Distance < 900.f)
        SetActorRotation(FRotator(0, ToPlayer.Rotation().Yaw, 0));
}

float ASoulwoodGoblin::TakeDamage(float DamageAmount, FDamageEvent const& Event,
    AController* EventInstigator, AActor* Causer)
{
    if (bDead) return 0.f;
    Health -= DamageAmount;
    if (Health <= 0.f)
    {
        bDead = true;
        PlayState(DeathAnimation, false);
        DropRewards();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        SetLifeSpan(2.f);
    }
    return DamageAmount;
}

void ASoulwoodGoblin::DropRewards()
{
    if (!IsValid(Target)) return;
    const ESoulwoodReward Types[] = { ESoulwoodReward::Gold, ESoulwoodReward::Fire,
        ESoulwoodReward::Beast, ESoulwoodReward::Angel };
    for (int32 i = 0; i < 4; ++i)
    {
        FVector DropAt = GetActorLocation() + FVector((i-1.5f)*82.f, (i%2 ? 65.f : -65.f), 115.f);
        ASoulwoodReward* Reward = GetWorld()->SpawnActor<ASoulwoodReward>(DropAt, FRotator::ZeroRotator);
        if (Reward) Reward->Initialize(Types[i], Target);
    }
}

ASoulwoodHero::ASoulwoodHero()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(42.f, 88.f);
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 680, 0);
    GetCharacterMovement()->MaxWalkSpeed = Soulwood::NormalSpeed;
    GetCharacterMovement()->MaxFlySpeed = 900.f;
    GetCharacterMovement()->BrakingDecelerationFlying = 2200.f;
    GetCharacterMovement()->AirControl = .8f;
    GetMesh()->SetRelativeLocation(FVector(0,0,-88));
    GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
    CameraArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraArm"));
    CameraArm->SetupAttachment(GetRootComponent());
    CameraArm->TargetArmLength = 355.f;
    CameraArm->SocketOffset = FVector(0, 70, 88);
    CameraArm->bUsePawnControlRotation = true;
    CameraArm->bEnableCameraLag = true;
    CameraArm->CameraLagSpeed = 11.f;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(CameraArm);
    Camera->SetFieldOfView(80.f);
    Bow = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EquippedBow"));
    Bow->SetupAttachment(GetRootComponent());
    Bow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Bow->SetRelativeLocation(FVector(85.f, -48.f, 30.f));
    Bow->SetRelativeRotation(FRotator(0.f, 90.f, 0.f));
    Bow->SetRelativeScale3D(FVector(.20f));
    Bow->SetVisibility(false);
    Wings = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AngelWings"));
    Wings->SetupAttachment(GetMesh(), TEXT("spine"));
    Wings->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Wings->SetVisibility(false);
    BootGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("LightningBoots"));
    BootGlow->SetupAttachment(GetRootComponent());
    BootGlow->SetRelativeLocation(FVector(0,0,-65));
    BootGlow->SetLightColor(FLinearColor(.02f,.4f,1.f));
    BootGlow->SetIntensity(0.f);
    BootGlow->SetAttenuationRadius(330.f);
}

void ASoulwoodHero::BeginPlay()
{
    Super::BeginPlay();
    GetMesh()->SetSkeletalMeshAsset(Soulwood::Asset<USkeletalMesh>(TEXT("/Game/SoulwoodOriginal/Characters/SK_Adventurer.SK_Adventurer")));
    Bow->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Game/SoulwoodOriginal/Meshes/SM_HunterBow.SM_HunterBow")));
    Wings->SetStaticMesh(Soulwood::Asset<UStaticMesh>(TEXT("/Game/SoulwoodOriginal/Meshes/SM_AngelWings.SM_AngelWings")));
    IdleAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_AdventurerSK_Adventurer_Hero_Idle.SK_AdventurerSK_Adventurer_Hero_Idle"));
    RunAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_AdventurerSK_Adventurer_Hero_Run.SK_AdventurerSK_Adventurer_Hero_Run"));
    BowAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_AdventurerSK_Adventurer_Hero_Bow_Draw.SK_AdventurerSK_Adventurer_Hero_Bow_Draw"));
    CastAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_AdventurerSK_Adventurer_Hero_Fireball_Cast.SK_AdventurerSK_Adventurer_Hero_Fireball_Cast"));
    FlightAnimation = Soulwood::Asset<UAnimSequence>(TEXT("/Game/SoulwoodOriginal/Characters/SK_AdventurerSK_Adventurer_Hero_Flight.SK_AdventurerSK_Adventurer_Hero_Flight"));
    PlayState(IdleAnimation, true);
}

void ASoulwoodHero::PlayState(UAnimSequence* Animation, bool bLoop)
{
    if (Animation && CurrentAnimation != Animation)
    {
        GetMesh()->PlayAnimation(Animation, bLoop);
        CurrentAnimation = Animation;
    }
}

void ASoulwoodHero::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    WingClock += DeltaTime;
    if (bSpeedActive)
    {
        Energy = FMath::Max(0.f, Energy - DeltaTime * (100.f/15.f));
        if (Energy <= 0.f) bSpeedActive = false;
    }
    else Energy = FMath::Min(100.f, Energy + DeltaTime * 11.f);
    GetCharacterMovement()->MaxWalkSpeed = bSpeedActive ? Soulwood::FastSpeed : Soulwood::NormalSpeed;
    GetCharacterMovement()->MaxFlySpeed = bSpeedActive ? 3000.f : 900.f;
    BootGlow->SetIntensity(bSpeedActive ? 1700.f : 0.f);
    if (bWingsUnlocked)
    {
        const float Frequency = bFlightActive ? 7.f : 2.f;
        const float Amplitude = bFlightActive ? 22.f : 7.f;
        Wings->SetRelativeRotation(FRotator(0, FMath::Sin(WingClock*Frequency)*Amplitude, 0));
    }
    Camera->SetFieldOfView(FMath::FInterpTo(Camera->FieldOfView,
        bFlightActive && GetVelocity().Size() > 400.f ? 93.f : 80.f, DeltaTime, 2.2f));
    if (bDrawing && SelectedAttack == 1) PlayState(BowAnimation, false);
    else if (GetWorld()->GetTimeSeconds() < CastAnimationUntil) PlayState(CastAnimation, false);
    else if (bFlightActive) PlayState(FlightAnimation, true);
    else if (GetVelocity().Size2D() > 40.f) PlayState(RunAnimation, true);
    else PlayState(IdleAnimation, true);
}

void ASoulwoodHero::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("MoveForward", this, &ASoulwoodHero::MoveForward);
    Input->BindAxis("MoveRight", this, &ASoulwoodHero::MoveRight);
    Input->BindAxis("LookYaw", this, &APawn::AddControllerYawInput);
    Input->BindAxis("LookPitch", this, &APawn::AddControllerPitchInput);
    Input->BindAxis("Rise", this, &ASoulwoodHero::Rise);
    Input->BindAction("Jump", IE_Pressed, this, &ACharacter::Jump);
    Input->BindAction("Jump", IE_Released, this, &ACharacter::StopJumping);
    Input->BindAction("Bow", IE_Pressed, this, &ASoulwoodHero::SelectBow);
    Input->BindAction("Fireball", IE_Pressed, this, &ASoulwoodHero::SelectFireball);
    Input->BindAction("Holster", IE_Pressed, this, &ASoulwoodHero::Holster);
    Input->BindAction("Speed", IE_Pressed, this, &ASoulwoodHero::ToggleSpeed);
    Input->BindAction("Flight", IE_Pressed, this, &ASoulwoodHero::ToggleFlight);
    Input->BindAction("Attack", IE_Pressed, this, &ASoulwoodHero::BeginAttack);
    Input->BindAction("Attack", IE_Released, this, &ASoulwoodHero::ReleaseAttack);
}

void ASoulwoodHero::MoveForward(float Value)
{
    if (FMath::IsNearlyZero(Value)) return;
    const FRotator View = Controller ? Controller->GetControlRotation() : GetActorRotation();
    const FVector Direction = bFlightActive ? View.Vector() : FRotationMatrix(FRotator(0,View.Yaw,0)).GetUnitAxis(EAxis::X);
    AddMovementInput(Direction, Value);
}

void ASoulwoodHero::MoveRight(float Value)
{
    if (FMath::IsNearlyZero(Value)) return;
    const FRotator View = Controller ? Controller->GetControlRotation() : GetActorRotation();
    AddMovementInput(FRotationMatrix(FRotator(0,View.Yaw,0)).GetUnitAxis(EAxis::Y), Value);
}

void ASoulwoodHero::Rise(float Value)
{
    if (bFlightActive && !FMath::IsNearlyZero(Value)) AddMovementInput(FVector::UpVector, Value);
}

void ASoulwoodHero::SelectBow() { SelectedAttack = SelectedAttack == 1 ? 0 : 1; Bow->SetVisibility(SelectedAttack == 1); }
void ASoulwoodHero::SelectFireball() { if (bFireballUnlocked) { SelectedAttack = 2; Bow->SetVisibility(false); } }
void ASoulwoodHero::Holster() { SelectedAttack = 0; Bow->SetVisibility(false); }
void ASoulwoodHero::ToggleSpeed() { if (bSpeedUnlocked && Energy > 1.f) bSpeedActive = !bSpeedActive; }

void ASoulwoodHero::ToggleFlight()
{
    if (!bWingsUnlocked) return;
    bFlightActive = !bFlightActive;
    GetCharacterMovement()->SetMovementMode(bFlightActive ? MOVE_Flying : MOVE_Falling);
    GetCharacterMovement()->bOrientRotationToMovement = !bFlightActive;
    if (bFlightActive) GetCharacterMovement()->Velocity *= .35f;
}

void ASoulwoodHero::BeginAttack()
{
    if (SelectedAttack == 0) return;
    bDrawing = true;
    DrawStart = GetWorld()->GetTimeSeconds();
    if (SelectedAttack == 2) CastAnimationUntil = DrawStart + .65f;
}

void ASoulwoodHero::ReleaseAttack()
{
    if (!bDrawing) return;
    bDrawing = false;
    const float Charge = FMath::Clamp((GetWorld()->GetTimeSeconds() - DrawStart)/1.2f, .2f, 1.f);
    FireProjectile(SelectedAttack == 2, Charge);
}

void ASoulwoodHero::FireProjectile(bool bIsFireball, float Charge)
{
    if (bIsFireball && !bFireballUnlocked) return;
    if (!Controller) return;
    FVector ViewLocation;
    FRotator ViewRotation;
    Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
    const FVector ViewEnd = ViewLocation + ViewRotation.Vector() * 30000.f;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SoulwoodAim), true, this);
    const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, ViewLocation, ViewEnd, ECC_Visibility, Query);
    const FVector AimPoint = bHit ? Hit.ImpactPoint : ViewEnd;
    const FVector Muzzle = GetActorLocation() + FVector(0,0,115) + ViewRotation.Vector()*85.f;
    const FVector Direction = (AimPoint-Muzzle).GetSafeNormal();
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.Instigator = this;
    ASoulwoodProjectile* Projectile = GetWorld()->SpawnActor<ASoulwoodProjectile>(Muzzle,
        Direction.Rotation(), Params);
    if (Projectile) Projectile->Configure(bIsFireball, Direction, bIsFireball ? 46.f : 27.f + Charge*22.f);
}

float ASoulwoodHero::TakeDamage(float DamageAmount, FDamageEvent const&, AController*, AActor*)
{
    Health = FMath::Max(0.f, Health - DamageAmount);
    if (Health <= 0.f)
    {
        Health = 100.f;
        SetActorLocation(FVector(-4200,0,140));
        GetCharacterMovement()->StopMovementImmediately();
    }
    return DamageAmount;
}

void ASoulwoodHero::Absorb(ESoulwoodReward Type)
{
    if (Type == ESoulwoodReward::Gold) Gold += 25;
    else if (Type == ESoulwoodReward::Fire) bFireballUnlocked = true;
    else if (Type == ESoulwoodReward::Beast) bSpeedUnlocked = true;
    else if (Type == ESoulwoodReward::Angel)
    {
        bWingsUnlocked = true;
        Wings->SetVisibility(true);
    }
    if (GEngine)
    {
        const TCHAR* Text = Type == ESoulwoodReward::Fire ? TEXT("FIREBALL UNLOCKED - press 2") :
            Type == ESoulwoodReward::Beast ? TEXT("BEAST SOUL - press Q for lightning speed") :
            Type == ESoulwoodReward::Angel ? TEXT("ANGEL WINGS - press F to fly") : TEXT("+25 GOLD ESSENCE");
        GEngine->AddOnScreenDebugMessage(-1, 4.f, FColor::White, Text);
    }
}

void ASoulwoodHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas) return;
    const ASoulwoodHero* Hero = Cast<ASoulwoodHero>(GetOwningPawn());
    if (!Hero) return;
    const float W = Canvas->SizeX, H = Canvas->SizeY;
    const FLinearColor Back(.018f,.022f,.028f,.78f);
    const FLinearColor Gold(.85f,.65f,.25f,1.f);
    DrawRect(Back, 25, 25, 240, 68);
    DrawText(TEXT("SOULWOOD   LV 1"), Gold, 38, 30, nullptr, 1.9f);
    DrawRect(FLinearColor(.25f,.04f,.04f), 38, 56, 210, 10);
    DrawRect(FLinearColor(.75f,.07f,.045f), 38, 56, 210*Hero->GetHealth()/100.f, 10);
    DrawRect(FLinearColor(.03f,.08f,.14f), 38, 73, 210, 8);
    DrawRect(FLinearColor(.03f,.45f,.9f), 38, 73, 210*Hero->GetEnergy()/100.f, 8);
    DrawLine(W*.5f-8,H*.5f,W*.5f-2,H*.5f,FLinearColor::White,1.5f);
    DrawLine(W*.5f+2,H*.5f,W*.5f+8,H*.5f,FLinearColor::White,1.5f);
    DrawLine(W*.5f,H*.5f-8,W*.5f,H*.5f-2,FLinearColor::White,1.5f);
    DrawLine(W*.5f,H*.5f+2,W*.5f,H*.5f+8,FLinearColor::White,1.5f);
    const FString Slots[] = { TEXT("1  BOW"), TEXT("2  FIRE"), TEXT("3  BEAST"), TEXT("4  WINGS") };
    for (int32 i=0; i<4; ++i)
    {
        const float X = W*.5f-224+i*116;
        const float Y = H-96;
        const bool bActive = i<2 ? Hero->GetSelectedAttack()==i+1 : (i==2 ? Hero->IsSpeedActive() : Hero->IsFlying());
        const bool bLocked = i==1 ? !Hero->HasFireball() : i==2 ? !Hero->HasSpeed() : i==3 ? !Hero->HasWings() : false;
        DrawRect(bActive ? FLinearColor(.25f,.17f,.045f,.94f) : Back, X,Y,108,60);
        DrawText(Slots[i], bLocked ? FLinearColor(.36f,.37f,.38f) : bActive ? Gold : FLinearColor::White,
            X+8,Y+10,nullptr,1.9f);
        if (bLocked) DrawText(TEXT("LOCKED"),FLinearColor(.45f,.45f,.45f),X+8,Y+36,nullptr,1.2f);
    }
    DrawText(FString::Printf(TEXT("Gold: %d"),Hero->GetGold()), Gold, W-190,30,nullptr,1.7f);
    if (Hero->HasSpeed())
        DrawText(FString::Printf(TEXT("Q  SPEED  %.0f%%"),Hero->GetEnergy()),FLinearColor(.2f,.65f,1.f),W-250,75,nullptr,1.5f);
    if (Hero->HasWings()) DrawText(TEXT("F  FLIGHT"),FLinearColor::White,W-180,115,nullptr,1.5f);
}

ASoulwoodGameMode::ASoulwoodGameMode()
{
    DefaultPawnClass = ASoulwoodHero::StaticClass();
    HUDClass = ASoulwoodHUD::StaticClass();
}

void ASoulwoodGameMode::BeginPlay()
{
    Super::BeginPlay();
    GetWorld()->SpawnActor<ASoulwoodGoblin>(FVector(-2500,0,130), FRotator(0,180,0));
}
