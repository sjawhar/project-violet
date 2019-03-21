using System.Collections;
using System.Collections.Generic;
using System.Security.Principal;
using UnityEngine;
using UnityEngine.Tilemaps;
using Gamekit2D;

namespace Buffalo
{
    public class PlayerCharacter : Gamekit2D.PlayerCharacter
    {
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
        }

        /////////////////
        // DOUBLE JUMP //
        /////////////////
        protected bool m_IsCanDoubleJump;

        public bool CheckForDoubleJump()
        {
            return PlayerInput.Instance.DoubleJump.Down;
        }

        public new bool CheckForGrounded()
        {
            bool grounded = base.CheckForGrounded();
            if (grounded) {
                m_IsCanDoubleJump = true;
            }
            return grounded;
        }

        public void DoubleJump()
        {
            if (!m_IsCanDoubleJump)
            {
                return;
            }

            SetVerticalMovement(jumpSpeed);
            m_IsCanDoubleJump = false;
        }
    }
}
