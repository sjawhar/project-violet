using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Gamekit2D
{
    public class DashSMB : SceneLinkedSMB<PlayerCharacter>
    {
        int m_HashAirborneDashState = Animator.StringToHash("AirborneDash");
    
        public override void OnSLStatePostEnter (Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            m_MonoBehaviour.ForceNotHoldingGun();
            m_MonoBehaviour.SetHorizontalMovement(m_MonoBehaviour.dashSpeed * m_MonoBehaviour.GetFacing());
        }

        public override void OnSLStateNoTransitionUpdate (Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            if (!m_MonoBehaviour.CheckForGrounded())
                animator.Play (m_HashAirborneDashState, layerIndex, stateInfo.normalizedTime);
        
            m_MonoBehaviour.GroundedHorizontalMovement(false);
        }
    }
}