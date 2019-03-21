using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using static Gamekit2D.InputComponent;

namespace Buffalo
{
    [Serializable]
    public class DoubleTapButton : InputButton
    {
        private int m_doubleTapStep = 0;
        private float m_doubleTapTimer = 0f;
        private float m_doubleTapSpeed = 0.25f;
        private bool m_AfterFixedUpdate = false;

        public DoubleTapButton(KeyCode key, XboxControllerButtons controllerButton)
            : base(key, controllerButton) { }

        public override void Get(bool fixedUpdateHappened, InputType inputType)
        {
            bool isHeld = Held;

            base.Get(fixedUpdateHappened, inputType);

            if (fixedUpdateHappened) {
                m_AfterFixedUpdate &= m_AfterFixedUpdateDown;
            }

            if (m_doubleTapStep == 0 && m_AfterFixedUpdateDown)
            {
                m_doubleTapTimer = m_doubleTapSpeed;
                m_doubleTapStep = 1;
            }
            else if (m_doubleTapStep == 3 && m_AfterFixedUpdateUp)
            {
                m_doubleTapStep = 0;
            }
            else if (m_doubleTapStep != 3 && m_doubleTapStep != 0 && m_doubleTapTimer <= 0)
            {
                m_doubleTapTimer = 0;
                m_doubleTapStep = 0;
            }
            else if (m_doubleTapStep == 1 && m_AfterFixedUpdateUp)
            {
                m_doubleTapTimer = m_doubleTapSpeed;
                m_doubleTapStep = 2;
            }
            else if (m_doubleTapStep == 2 && m_AfterFixedUpdateDown)
            {
                m_doubleTapTimer = 0;
                m_doubleTapStep = 3;
                m_AfterFixedUpdate = true;
                isHeld = true;
            }

            if (m_doubleTapTimer > 0)
            {
                m_doubleTapTimer -= Time.deltaTime;
            }

            Down = m_AfterFixedUpdate;
            Held = isHeld & m_AfterFixedUpdateHeld;
            Up |= !(Down || Held);
        }
    }
}
