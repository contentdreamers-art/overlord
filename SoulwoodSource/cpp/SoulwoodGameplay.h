#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "SoulwoodGameplay.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UProjectileMovementComponent;
class USpringArmComponent;
class UCameraComponent;
class ASoulwoodHero;

UENUM(BlueprintType)
enum class ESoulwoodReward : uint8 { Gold, Fire, Beast, Angel };

UCLASS()
class SOULWOODGAME_API ASoulwoodProjectile : public AActor
{
    GENERATED_BODY()
public:
    ASoulwoodProjectile();
    void Configure(bool bIsFireball, const FVector& Velocity, float Damage);
protected:
    UFUNCTION() void OnOverlap(UPrimitiveComponent* Overlapped, AActor* Other,
        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& Hit);
    UPROPERTY(VisibleAnywhere) TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Glow;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UProjectileMovementComponent> Movement;
    bool bFireball = false;
    float HitDamage = 25.f;
};

UCLASS()
class SOULWOODGAME_API ASoulwoodReward : public AActor
{
    GENERATED_BODY()
public:
    ASoulwoodReward();
    void Initialize(ESoulwoodReward InType, ASoulwoodHero* InOwner);
    virtual void Tick(float DeltaTime) override;
protected:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Glow;
    UPROPERTY() TObjectPtr<ASoulwoodHero> Recipient;
    ESoulwoodReward RewardType = ESoulwoodReward::Gold;
    float TimeAlive = 0.f;
    FVector StartLocation;
};

UCLASS()
class SOULWOODGAME_API ASoulwoodGoblin : public ACharacter
{
    GENERATED_BODY()
public:
    ASoulwoodGoblin();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& Event,
        class AController* Instigator, AActor* Causer) override;
protected:
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Sword;
    UPROPERTY() TObjectPtr<ASoulwoodHero> Target;
    float Health = 90.f;
    float AttackClock = 0.f;
    float AttackCooldown = 0.f;
    bool bWindingUp = false;
    bool bDead = false;
    void DropRewards();
};

UCLASS()
class SOULWOODGAME_API ASoulwoodHero : public ACharacter
{
    GENERATED_BODY()
public:
    ASoulwoodHero();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& Event,
        class AController* Instigator, AActor* Causer) override;
    void Absorb(ESoulwoodReward Type);
    float GetHealth() const { return Health; }
    float GetEnergy() const { return Energy; }
    bool HasFireball() const { return bFireballUnlocked; }
    bool HasSpeed() const { return bSpeedUnlocked; }
    bool HasWings() const { return bWingsUnlocked; }
    bool IsSpeedActive() const { return bSpeedActive; }
    bool IsFlying() const { return bFlightActive; }
    int32 GetSelectedAttack() const { return SelectedAttack; }
    int32 GetGold() const { return Gold; }
protected:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> CameraArm;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Bow;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Wings;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> BootGlow;
    float Health = 100.f;
    float Energy = 100.f;
    float DrawStart = 0.f;
    float WingClock = 0.f;
    int32 Gold = 0;
    int32 SelectedAttack = 0;
    bool bFireballUnlocked = false;
    bool bSpeedUnlocked = false;
    bool bWingsUnlocked = false;
    bool bSpeedActive = false;
    bool bFlightActive = false;
    bool bDrawing = false;
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Rise(float Value);
    void SelectBow();
    void SelectFireball();
    void Holster();
    void ToggleSpeed();
    void ToggleFlight();
    void BeginAttack();
    void ReleaseAttack();
    void FireProjectile(bool bFireball, float Charge);
};

UCLASS()
class SOULWOODGAME_API ASoulwoodHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

UCLASS()
class SOULWOODGAME_API ASoulwoodGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASoulwoodGameMode();
    virtual void BeginPlay() override;
};
