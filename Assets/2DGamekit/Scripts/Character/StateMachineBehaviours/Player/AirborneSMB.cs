using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Gamekit2D
{
    public class AirborneSMB : SceneLinkedSMB<PlayerCharacter>
    {
        public override void OnSLStateNoTransitionUpdate (Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            m_MonoBehaviour.UpdateFacing();
            if (m_MonoBehaviour.CheckForDoubleJump())
            {
                m_MonoBehaviour.DoubleJump();
            }
            else
            {
                m_MonoBehaviour.UpdateJump();
            }
            m_MonoBehaviour.AirborneHorizontalMovement();
            m_MonoBehaviour.AirborneVerticalMovement();
            m_MonoBehaviour.CheckForGrounded();
            m_MonoBehaviour.CheckForHoldingGun();
            if (m_MonoBehaviour.CheckForDashInput())
            {
                m_MonoBehaviour.Dash();
            }
            else if(m_MonoBehaviour.CheckForMeleeAttackInput())
            {
                m_MonoBehaviour.MeleeAttack ();
            }
            m_MonoBehaviour.CheckAndFireGun ();
            m_MonoBehaviour.CheckForCrouching ();
        }
    }
}