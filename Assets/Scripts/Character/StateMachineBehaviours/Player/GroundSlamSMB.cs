using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Gamekit2D;

namespace Buffalo
{
    public class GroundSlamSMB : SceneLinkedSMB<PlayerCharacter>
    {
        public override void OnSLStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            m_MonoBehaviour.ForceNotHoldingGun();
        }

        public override void OnSLStatePostEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            m_MonoBehaviour.SetHorizontalMovement(0);
            m_MonoBehaviour.SetVerticalMovement(-m_MonoBehaviour.groundSlamSpeed);
        }

        public override void OnSLStateNoTransitionUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            m_MonoBehaviour.CheckForGrounded();
        }
    }
}
