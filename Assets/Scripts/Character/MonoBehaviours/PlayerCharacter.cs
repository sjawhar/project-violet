using System.Collections;
using System.Collections.Generic;
using System.Security.Principal;
using UnityEngine;
using UnityEngine.Tilemaps;
using Gamekit2D;

namespace Violet
{
    public class PlayerCharacter : Gamekit2D.PlayerCharacter
    {
        public CharacterController2D characterController
        {
            get { return m_CharacterController2D; }
        }

        void Start()
        {
            hurtJumpAngle = Mathf.Clamp(hurtJumpAngle, k_MinHurtJumpAngle, k_MaxHurtJumpAngle);
            m_TanHurtJumpAngle = Mathf.Tan(Mathf.Deg2Rad * hurtJumpAngle);
            m_FlickeringWait = new WaitForSeconds(flickeringDuration);

            meleeDamager.DisableDamage();

            m_ShotSpawnGap = 1f / shotsPerSecond;
            m_NextShotTime = Time.time;
            m_ShotSpawnWait = new WaitForSeconds(m_ShotSpawnGap);

            if (!Mathf.Approximately(maxHorizontalDeltaDampTime, 0f))
            {
                float maxHorizontalDelta = maxSpeed * cameraHorizontalSpeedOffset + cameraHorizontalFacingOffset;
                m_CamFollowHorizontalSpeed = maxHorizontalDelta / maxHorizontalDeltaDampTime;
            }

            if (!Mathf.Approximately(maxVerticalDeltaDampTime, 0f))
            {
                float maxVerticalDelta = cameraVerticalInputOffset;
                m_CamFollowVerticalSpeed = maxVerticalDelta / maxVerticalDeltaDampTime;
            }

            SceneLinkedSMB<Gamekit2D.PlayerCharacter>.Initialise(m_Animator, this);
            SceneLinkedSMB<PlayerCharacter>.Initialise(m_Animator, this);

            m_StartingPosition = transform.position;
            m_StartingFacingLeft = GetFacing() < 0.0f;
        }

        protected bool m_IsGrounded = false;
        public new bool CheckForGrounded()
        {
            m_IsGrounded = base.CheckForGrounded();
            if (m_IsGrounded) {
                m_IsCanDoubleJump = true;
                m_IsCanGroundSlam = true;
            }
            return m_IsGrounded;
        }

        /////////////
        // DASHING //
        /////////////
        public float dashSpeed = 30f;
        protected readonly int m_HashDashPara = Animator.StringToHash("Dash");

        public bool CheckForDashInput()
        {
            return PlayerInput.Instance.Dash.Down;
        }

        public void Dash()
        {
            m_Animator.SetTrigger(m_HashDashPara);
            Resonator.Resonate(ResonateColor.Red);
        }

        /////////////////
        // DOUBLE JUMP //
        /////////////////
        protected bool m_IsCanDoubleJump = false;

        public bool CheckForDoubleJump()
        {
            if (!m_IsCanDoubleJump)
            {
                return false;
            }
            return PlayerInput.Instance.Jump.Down;
        }

        public void DoubleJump()
        {
            SetVerticalMovement(jumpSpeed);
            m_IsCanDoubleJump = false;
            Resonator.Resonate(ResonateColor.Green);
        }

        /////////////////
        // GROUND SLAM //
        /////////////////
        public float groundSlamSpeed = 30f;
        protected bool m_IsCanGroundSlam = false;
        protected readonly int m_HashGroundSlamPara = Animator.StringToHash("Ground Slam");

        public bool CheckForGroundSlam()
        {
            if (m_IsGrounded || !m_IsCanGroundSlam)
            {
                return false;
            }
            return PlayerInput.Instance.GroundSlam.Down;
        }

        public void GroundSlam()
        {
            m_IsCanGroundSlam = false;
            m_Animator.SetTrigger(m_HashGroundSlamPara);
            Resonator.Resonate(ResonateColor.Blue);
        }
    }
}
