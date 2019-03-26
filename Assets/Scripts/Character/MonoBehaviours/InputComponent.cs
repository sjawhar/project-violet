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

        bool m_AfterFixedUpdate = false;

        public DoubleTapButton(KeyCode key, XboxControllerButtons controllerButton)
            : base(key, controllerButton) { }

        public new void Get(bool fixedUpdateHappened, InputType inputType)
        {
            bool isHeld = Held;

            base.Get(fixedUpdateHappened, inputType);

            if (fixedUpdateHappened) {
                m_AfterFixedUpdate &= Down;
            }

            if (m_doubleTapStep == 0 && Down)
            {
                m_doubleTapTimer = m_doubleTapSpeed;
                m_doubleTapStep = 1;
            }
            else if (m_doubleTapStep == 3 && Up)
            {
                m_doubleTapStep = 0;
            }
            else if (m_doubleTapStep != 3 && m_doubleTapStep != 0 && m_doubleTapTimer <= 0)
            {
                m_doubleTapTimer = 0;
                m_doubleTapStep = 0;
            }
            else if (m_doubleTapStep == 1 && Up)
            {
                m_doubleTapTimer = m_doubleTapSpeed;
                m_doubleTapStep = 2;
            }
            else if (m_doubleTapStep == 2 && Down)
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
            Held &= isHeld;
            Up |= !(Down || Held);
        }
    }
}
